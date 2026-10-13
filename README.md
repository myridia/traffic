<img src="traffic.svg" alt="traffic" width="120">

# traffic
see clone activity of all repositories

```bash
git clone git@github.com:myridia/traffic.git
git clone https://github.com/veto8/traffic.git
cd traffic
poetry install
export GITHUB_TOKEN=ghp_Mxxxxxx
poetry run python main.py --owner myridia --by clones --csv clones.csv
poetry run python main.py --owner myridia --by stars --csv stars.csv
```
