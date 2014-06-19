# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.require_version '>= 1.5.1'

Vagrant.configure('2') do |config|
  config.vm.define 'tower-precise', primary: true do |precise|
    precise.vm.box = "precise-server-cloudimg-amd64"
    precise.vm.box_url = "http://cloud-images.ubuntu.com/vagrant/precise/current/precise-server-cloudimg-amd64-vagrant-disk1.box"

    precise.vm.hostname = 'tower-precise'

    precise.vm.network :private_network, ip: '33.33.33.13'
    precise.vm.network :forwarded_port, guest: 80, host: 8013
    precise.vm.network :forwarded_port, guest: 8080, host: 8080
    precise.vm.network :forwarded_port, guest: 15672, host: 15013
    precise.vm.network :forwarded_port, guest: 24013, host: 24013

    precise.vm.synced_folder '.', '/var/ansible/tower/',
      :mount_options => [ 'gid=5853', 'dmode=2775' ]

    precise.vm.provider :virtualbox do |vb|
      vb.customize ["modifyvm", :id, "--memory", '1024']
    end
  end

  config.ssh.forward_agent = true

  config.vm.provision 'ansible' do |ansible|
    ansible.extra_vars = {
      'development' => true,
      'target_hosts' => 'vagrant',
      'target_user' => 'vagrant',
      'vagrant' => true,
      'vagrant_host_user' => ENV['USER'],
    }
    ansible.inventory_path = 'tools/dev_setup/inventory'
    ansible.playbook = 'tools/dev_setup/playbook.yml'
    ansible.verbose = 'v'
  end
end
