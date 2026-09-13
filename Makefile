install:
		pip3 install mlx-2.2-py3-none-any.whl

run:
		python3 a-maze-ing.py config.txt

debug:
		python3 -m pdb a_maze_ing.py config.txt

clean:
		rm -rf __pycache__ .mypy_cache

lint:
		flake8 .
		mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
		flake8 .
		mypy . --strict
