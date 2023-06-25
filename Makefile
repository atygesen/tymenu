
docker-up:
	docker compose up \
		--detach

docker-stop:
	docker compose stop

docker-down:
	docker compose down \
		--remove-orphans

docker-down-clean:
	docker compose down \
		--remove-orphans \
		--volumes


.PHONY: \
	docker-up \
	docker-stop \
	docker-down \
	docker-down-clean
