1.  Copy those two files to `.git/hooks`.
2.  Create copies of the template `client_secrets.json` files and name them `_client_secrets.json`
3.  Edit the `client_secrets.json` files with your actual data.
4.  Commit as you normally would, the pre/post commit scripts will make
    sure that only the template files are commited and not your actual secrets.