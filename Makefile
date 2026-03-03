VER=	$(shell uv version --short)

lint:
	uv run ruff check --select=I . && uv run ruff format --check .

format:
	uv run ruff check --fix --select=I . && uv run ruff format .

release:
	git tag v$(VER)
	git push origin v$(VER)

release-minor:
	uv version --bump minor

.PHONY: lint format release release-minor
