# this assumes you have git already installed, and just need to re-add more packages to the env. 
# this assumes you have heroku cli installed too.
# change the name of the dash app at every run.

conda activate talapas-calculator

# create environment
pip freeze > requirements.txt

git add .
git commit -m "added more feature and styling."
git push heroku master
heroku ps:scale web=1