up:
	docker compose up \
		--detach

up-build:
	docker compose up \
		--detach \
		--build

stop:
	docker compose stop

down:
	docker compose down \
		--remove-orphans

down-clean:
	docker compose down \
		--remove-orphans \
		--volumes


.PHONY: \
	up \
	stop \
	down \
	up-build \
	down-clean
