<h4>Homework:</h4>

1. Run postgresql in docker.
2. Expand test coverage:
- Post: creation. Preconditions: prepared test data
- Delete: deletion. Preconditions: created user
- Patch: change. Preconditions: created user

Optional:
- Get after create, update
- 405 error test: Preconditions: nothing needed
- 404 422 errors on delete patch
- 404 on deleted user
- user flow: create, read, update, delete
- test data validity (email, URL)
- send model without field for creation