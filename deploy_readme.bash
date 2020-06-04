# this assumes you have git already installed, and just need to re-add more packages to the env. 
# this assumes you have heroku cli installed too.
# change the name of the dash app at every run.

# conda activate talapas-calculator

# create environment
pip freeze > requirements.txt
# heroku create su-calc # name of the app
git add -A # add only updated files.
git commit -m "app env "
git push heroku master
heroku ps:scale web=1

# pip uninstall mkl_fft

# the difficulty is to subset the packages compatible with the app. a lot of mkl packages lead to bad environments, so we removed those in the requirements.txt file. for example mkl_fft is for fourier transforms that we do not use.
# we can also continue to remove more apps (like numpy) that were never used to reduce app size.