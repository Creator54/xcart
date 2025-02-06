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
        
        xcart-src = pkgs.fetchFromGitHub {
          owner = "creator54";
          repo = "xcart";
          rev = "main";
          sha256 = "sha256-dyf1QTBGuXR6AM+JDRCKys61YoU8i3XfDPv3vnCTu/4=";
        };
      in
      {
        packages = {
          default = self.packages.${system}.xcart;
          xcart = pkgs.writeShellScriptBin "xcart" ''
            # Enter the Python shell environment and run uvicorn
            ${pkgs.bashInteractive}/bin/bash -c '
              # Create working directory
              WORK_DIR="$HOME/.local/share/xcart"
              
              # Remove existing directory if it exists
              rm -rf "$WORK_DIR"
              mkdir -p "$WORK_DIR"
              
              # Copy source files to working directory with proper permissions
              cp -r ${xcart-src}/* "$WORK_DIR/"
              chmod -R u+w "$WORK_DIR"
              cd "$WORK_DIR"
              
              # Set environment variables
              export OTEL_RESOURCE_ATTRIBUTES=service.name=xcart-v1
              export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"
              
              # Add required libraries to LD_LIBRARY_PATH
              export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
              
              # Run the application
              exec uvicorn app.main:app --reload --port 8000
            '
          '';
        };

        devShells.default = pythonShell.overrideAttrs (oldAttrs: {
          buildInputs = oldAttrs.buildInputs ++ [
            pkgs.stdenv.cc.cc.lib  # Add libstdc++
          ];
          
          shellHook = oldAttrs.shellHook + ''
            # Check if we're already in a xcart directory
            if [ ! -f "app/main.py" ]; then
              echo "Setting up XCart in current directory..."
              
              # Copy source files to current directory
              cp -r ${xcart-src}/* .
              chmod -R u+w .
            fi
            
            # Set environment variables
            export OTEL_RESOURCE_ATTRIBUTES=service.name=xcart-v1
            export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
          '';
        });
      }
    );
}
