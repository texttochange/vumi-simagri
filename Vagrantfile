Vagrant::configure("2") do |config|

  config.vm.hostname = "vagrant"
  config.vm.box = "miniaggregator3"
  config.vm.box_url = "file:///Users/olivier/Desktop/SIMAgri/Vagrant_Boxes/trusty64_miniaggregator.box"

  config.vm.network "forwarded_port", guest:80, host:4567   
  config.vm.network "forwarded_port", guest:9010, host:4568

  #to run the tests in your host env
  config.vm.network "forwarded_port", guest:6379, host:6379

  #to allow pushing messages to the default transports
  config.vm.network "forwarded_port", guest:3330, host:3330
  config.vm.network "forwarded_port", guest:3331, host:3331
  config.vm.network "forwarded_port", guest:3332, host:3333

  config.vm.network "private_network", ip:"10.11.12.13"
  config.vm.synced_folder "transports", "/var/vumi-simagri/transports",  type:"nfs"
  config.vm.synced_folder "dispatchers", "/var/vumi-simagri/dispatchers", type:"nfs"
  config.vm.synced_folder "middlewares", "/var/vumi-simagri/middlewares", type:"nfs"
  config.vm.synced_folder "etc", "/var/vumi-simagri/etc", type:"nfs"
  config.vm.synced_folder "log", "/var/vumi-simagri/log", type:"nfs"

end
