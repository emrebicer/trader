# shell.nix
{ pkgs ? import <nixpkgs> {} }:
let
  python-packages = ps: with ps; [
    requests
    rich
    python-lsp-server
    python-lsp-ruff
  ];
  pythonEnv = pkgs.python3.withPackages python-packages;
in 
pkgs.mkShell{
  packages = [
    pythonEnv
  ];
}
