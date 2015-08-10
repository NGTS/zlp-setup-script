# -*- mode: ruby -*-
# vi: set ft=ruby :

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure(2) do |config|
  config.vm.box = "debian/jessie64"
  config.vm.provision "ansible" do |ansible|
    ansible.playbook = 'site.yml'
  end
  config.vm.provider "virtualbox" do |vb|
    vb.cpus = 2
  end
end
