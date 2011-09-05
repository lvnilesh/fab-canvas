from __future__ import with_statement
from fabric.api import env, roles, run, put, local, settings, abort
from fabric.contrib.console import confirm 
from openstack.compute import Compute
compute = Compute(username='rackspace-username', apikey='your-rackspace-api-key-goes-here')

TargetDomain = 'canvas.nescorp.us'
# also need to change in canvas.site, outgoing_mail.yml and domain.yml
env.user = 'nilesh' 

@roles('web')
def test():
    print TargetDomain
    rassi = "ping " +TargetDomain
    local(rassi)
    
# Define sets of servers as roles
env.roledefs = {
    'web': [TargetDomain],
    'cache': ['124.124.124.124', '125.125.125.125']
}

# This will instantiate an Ubuntu Lucid server with 2GB RAM in your rackspace cloud
@roles('web')
def create_server():
    fl = compute.flavors.find(ram=2048)
    im = compute.images.find(id=49) # openstack-compute image-list - we are using ubuntu 10.04 lucid
    compute.servers.create(TargetDomain, image=im, flavor=fl)

# fab prep prepares cloud server for password-less SSH access
@roles('web')
def prep():
    env.user = 'root' 
    local('rm -f ~/.ssh/known_hosts')
    local('echo change root passwd')
    run('passwd')
    local('echo adding new user nilesh')
    run('adduser nilesh')
    local('echo allow sudo permissions for nilesh')
    run('echo "nilesh ALL=(ALL) ALL" >> /etc/sudoers')    
    env.user = 'nilesh' 
    local('echo Now working as nilesh')
    run('mkdir -p /home/nilesh/.ssh')
    put('/Users/nilesh/.ssh/id_dsa.pub')
    run('mv id_dsa.pub /home/nilesh/.ssh/authorized_keys')
    run('echo "export GEM_HOME=/home/nilesh/gems" >> /home/nilesh/.bashrc')
    run('set |grep HOME')
    run('sudo apt-get update && sudo apt-get -y dist-upgrade')
    run('sudo hostname '+ TargetDomain)
    run('sudo sh -c "hostname > /etc/hostname"')
    rassi = "s/localhost.localdomain/" + TargetDomain + "/"
    bhago = "sudo perl -p -i -e " + rassi + " /etc/hosts"
    run(bhago)    
    run('sudo reboot')

# fab canvas will setup canvas in production mode - https://github.com/instructure/canvas-lms/wiki/Production-Start
# Restrict the function to the 'web' role
@roles('web')
def canvas():
    run('cat /etc/hosts')
    run('sudo apt-get update')
    run('sudo apt-get install -y openssh-server git-core mysql-server')
    run('sudo mkdir -p /var/rails') # setup into /var/rails/canvas by cloning from git
    run('cd /var/rails; sudo git clone https://github.com/instructure/canvas-lms.git canvas')
    run('sudo chown -R nilesh /var/rails/canvas')
    run('sudo apt-get update')
    run('sudo apt-get -y install ruby ruby-dev zlib1g-dev libxml2-dev libmysqlclient-dev libxslt1-dev libsqlite3-dev nano imagemagick libpq-dev rake rubygems libhttpclient-ruby irb') #FAILED on chunkhost rake rubygems libhttpclient-ruby irb 
    run('sudo apt-get install -y libopenssl-ruby') # rake db:import failed without this with "No Such File to Load: net/https"
    run('sudo apt-get install -y --reinstall python-software-properties && sudo dpkg-reconfigure python-software-properties')
    run('sudo apt-add-repository ppa:maco.m/ruby')
    run('sudo apt-get update')
    run('sudo apt-get install -y rubygems')
    run('mkdir -p /home/nilesh/gems')
    run('cd /var/rails/canvas; export GEM_HOME=/home/nilesh/gems; gem install bundler; $GEM_HOME/bin/bundle install')
    run('cd /var/rails/canvas; for config in amazon_s3 database delayed_jobs domain file_store outgoing_mail security; do cp config/$config.yml.example config/$config.yml; done')
    put('database.yml')
    run('sudo mv database.yml /var/rails/canvas/config/')
    put('outgoing_mail.yml')
    run('sudo mv outgoing_mail.yml /var/rails/canvas/config/')
    put('domain.yml')
    run('sudo mv domain.yml /var/rails/canvas/config/')
    put('mysql-script.sh')
    run('sh mysql-script.sh')
    run('cd /var/rails/canvas; export GEM_HOME=/home/nilesh/gems; RAILS_ENV=production $GEM_HOME/bin/bundle exec rake db:initial_setup')
    run('sudo adduser --disabled-password --gecos canvas canvasuser')
    run('cd /var/rails/canvas; sudo mkdir -p log tmp/pids public/assets public/stylesheets/compiled')
    run('cd /var/rails/canvas; sudo touch Gemfile.lock')
    run('cd /var/rails/canvas; sudo chown -R canvasuser config/environment.rb log tmp public/assets public/stylesheets/compiled Gemfile.lock')
    run('cd /var/rails/canvas; sudo chown canvasuser config/*.yml')
    run('cd /var/rails/canvas; sudo chmod 400 config/*.yml')
    run('sudo apt-get update')
    run('sudo apt-get -y install apache2 libapache2-mod-passenger')    
    sutali = "echo ServerName " + TargetDomain + " > /etc/apache2/httpd.conf"
    dhaga = "sudo sh -c '" + sutali + "'"
    run(dhaga)
    run('sudo a2enmod rewrite passenger ssl')
    run('sudo /etc/init.d/apache2 restart')
    run('sudo unlink /etc/apache2/sites-enabled/000-default') 
    put('canvas.site')
    run('sudo mv canvas.site /etc/apache2/sites-available/canvas')
    run('sudo a2ensite canvas')
    run('wget http://redis.googlecode.com/files/redis-2.2.12.tar.gz')
    run('tar xzf redis-2.2.12.tar.gz')
    run('cd redis-2.2.12; make')
    put('cache_store.yml')
    run('mv cache_store.yml /var/rails/canvas/config/')
    run('cd /var/rails/canvas; echo $GEM_HOME | sudo tee config/GEM_HOME')
    run('sudo ln -s /var/rails/canvas/script/canvas_init /etc/init.d/canvas_init')
    run('sudo update-rc.d canvas_init defaults')
    run('sudo /etc/init.d/canvas_init start')
    run('sudo /etc/init.d/apache2 restart')

#and Canvas should work now!!!