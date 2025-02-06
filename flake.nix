{
  description = "XCart API - FastAPI-based e-commerce REST API";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-24.11";
    flake-utils.url = "github:numtide/flake-utils";
    nix-shells.url = "github:creator54/nix-shells";
  };

  outputs = { self, nixpkgs, flake-utils, nix-shells }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        pythonShell = import "${nix-shells}/devShells/python.nix" { inherit pkgs; };
        signozShell = import "${nix-shells}/devShells/signoz.nix" { inherit pkgs; };
        signoz = signozShell.buildInputs;
        
        xcart-src = pkgs.fetchFromGitHub {
          owner = "creator54";
          repo = "xcart";
          rev = "main";
          sha256 = "sha256-dyf1QTBGuXR6AM+JDRCKys61YoU8i3XfDPv3vnCTu/4=";
        };

        # Create a derivation for the xcart service
        xcart-service = pkgs.writeShellApplication {
          name = "xcart-service";
          runtimeInputs = [ pkgs.python3 ];
          text = ''
            # Add required libraries to LD_LIBRARY_PATH
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
            
            # Default values
            OTLP_ENDPOINT="''${1:-http://localhost:4317}"
            OTLP_TOKEN="''${2:-}"
            
            export OTEL_RESOURCE_ATTRIBUTES=service.name=xcart-v1
            export OTEL_EXPORTER_OTLP_ENDPOINT="$OTLP_ENDPOINT"
            
            if [ -n "$OTLP_TOKEN" ]; then
              export OTEL_EXPORTER_OTLP_HEADERS="signoz-access-token=$OTLP_TOKEN"
            fi
            
            echo -e "\n📊 OpenTelemetry Configuration:"
            echo "  • Endpoint: $OTLP_ENDPOINT"
            if [ -n "$OTLP_TOKEN" ]; then
              echo "  • Access Token: Configured"
            else
              echo "  • Access Token: Not required (local SigNoz)"
            fi
            
            echo -e "\n🚀 Starting XCart Server..."
            echo "  • API Documentation: http://localhost:8000/docs"
            echo "  • Metrics Dashboard: http://localhost:3301"
            
            WORK_DIR="$HOME/.local/share/xcart"
            rm -rf "$WORK_DIR"
            mkdir -p "$WORK_DIR"
            cp -r ${xcart-src}/* "$WORK_DIR/"
            chmod -R u+w "$WORK_DIR"
            cd "$WORK_DIR"
            
            exec uvicorn app.main:app --reload --port 8000
          '';
        };

        # Create a derivation for the health check
        signoz-health-check = pkgs.writeShellApplication {
          name = "signoz-health-check";
          runtimeInputs = [ pkgs.curl ];
          text = ''
            attempt=1
            max_attempts=30
            while [ $attempt -le $max_attempts ]; do
              if curl -s http://localhost:3301 > /dev/null; then
                echo "SigNoz is ready!"
                exit 0
              fi
              echo "Waiting for SigNoz... attempt $attempt/$max_attempts"
              sleep 2
              attempt=$((attempt + 1))
            done
            echo "SigNoz failed to start"
            exit 1
          '';
        };

        # Create a wrapper that combines both services
        xcart = pkgs.writeShellApplication {
          name = "xcart";
          runtimeInputs = [ pkgs.curl ] ++ signozShell.buildInputs;
          text = ''
            # Get the OTLP endpoint from args or default to localhost
            OTLP_ENDPOINT="''${1:-http://localhost:4317}"
            
            # Only check and start local SigNoz if using localhost
            if [[ "$OTLP_ENDPOINT" == *"localhost"* ]]; then
              if curl -s http://localhost:3301 > /dev/null; then
                echo -e "\n✅ SigNoz is already running"
                echo "  • Dashboard: http://localhost:3301"
              else
                echo -e "\n🚀 Starting SigNoz..."
                # Use signoz's start-signoz script
                start-signoz
                ${signoz-health-check}/bin/signoz-health-check
              fi
            fi

            echo -e "\n🔄 Starting XCart with SigNoz integration..."
            exec ${xcart-service}/bin/xcart-service "$@"
          '';
        };
      in
      {
        packages = {
          inherit xcart xcart-service signoz-health-check;
          default = xcart;
        };

        devShells.default = pkgs.mkShell {
          buildInputs = (pythonShell.buildInputs or []) ++ 
                       (signozShell.buildInputs or []) ++ [
            pkgs.stdenv.cc.cc.lib  # Only needed for Python's grpcio
          ];

          nativeBuildInputs = (pythonShell.nativeBuildInputs or []) ++
                             (signozShell.nativeBuildInputs or []);
          
          shellHook = ''
            ${signozShell.shellHook or ""}
            ${pythonShell.shellHook or ""}
            
            # Check if we're already in a xcart directory
            if [ ! -f "app/main.py" ]; then
              echo "Setting up XCart in current directory..."
              cp -r ${xcart-src}/* .
              chmod -R u+w .
            fi

            # Set OpenTelemetry configuration for local development
            export OTEL_RESOURCE_ATTRIBUTES=service.name=xcart-v1
            export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
            
            echo -e "\n📌 Available commands:"
            echo "  • start-signoz  - Start SigNoz monitoring"
            echo "  • stop-signoz   - Stop SigNoz services"
            echo "  • uvicorn app.main:app --reload --port 8000  - Start XCart"
          '';
        };
      }
    );
}
