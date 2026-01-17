{
  description = "CLI controller for IKEA Idasen standing desks";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python3;

        venvDir = "$HOME/.cache/idasen-desk/venv";
        scriptDir = "${self}";

        deskWrapper = pkgs.writeShellScriptBin "desk" ''
          set -e
          VENV="${venvDir}"
          if [ ! -d "$VENV" ]; then
            ${python}/bin/python3 -m venv "$VENV"
            "$VENV/bin/pip" install --quiet bleak
          fi
          "$VENV/bin/python3" "${scriptDir}/desk.py" "$@"
        '';

        stand = pkgs.writeShellScriptBin "stand" ''
          exec ${deskWrapper}/bin/desk move stand
        '';

        sit = pkgs.writeShellScriptBin "sit" ''
          exec ${deskWrapper}/bin/desk move sit
        '';

        combined = pkgs.symlinkJoin {
          name = "idasen-desk";
          paths = [ deskWrapper stand sit ];
        };
      in
      {
        packages = {
          default = combined;
          desk = deskWrapper;
          inherit stand sit;
        };

        apps.default = {
          type = "app";
          program = "${deskWrapper}/bin/desk";
        };

        devShells.default = pkgs.mkShell {
          buildInputs = [
            python
            pkgs.python3Packages.pip
          ];
        };
      }
    );
}
