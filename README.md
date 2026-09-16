Ainda desenvolvendo esse projeto :)

possiveis dependencias para rodar o programa
sudo apt update
sudo apt install -y libx11-6 libxext6 libxcb-keysyms1 libvulkan1
pip3 install mlx-2.2-py3-none-any.whl
pip3 install flake8 mypy
pip3 install python3
pip3 install pytest


Vamos utilizar como algoritmo de geração de labirinto o Recursive Backtracker
bitwise para rastrear as paredes -- entre 0 - 3, sendo (Norte, Leste, Sul, Oeste)