.PHONY: run test docker clean

run:
	python3 app.py

test:
	python3 -m unittest discover -s tests -v

docker:
	docker build -t tripwatch-ai .

clean:
	rm -rf __pycache__ tests/__pycache__ data/*.db data/*.db-wal data/*.db-shm
