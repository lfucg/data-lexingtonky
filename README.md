## LFUCG - CKAN

### Requirements

#### ChefDK

ChefDK includes several utilities for creating and managing chef resources.  To install it, navigate [here](https://docs.chef.io/install_dk.html#get-package-run-installer) and complete the ___Get Package, Run Installer___ and ___Set System Ruby___ sections.

#### VirtualBox / Vagrant

VirtualBox and Vagrant will provide you with a virtual machine to provision using this cookbook.  You can download VirtualBox [here](https://www.virtualbox.org/wiki/Downloads) and Vagrant [here](https://www.vagrantup.com/downloads.html).

Once those are installed, install a couple of vagrant chef plugins:

```bash
$ vagrant plugin install vagrant-berkshelf
$ vagrant plugin install vagrant-omnibus
```

### Development

After installing `vagrant` and the chef plugins, you can start a vagrant vm using the ruby script `start_vm.rb`:

```bash
$ ./start_vm.rb
Initializing cookbook submodule ...     [DONE]
Starting vm ...
Bringing machine 'default' up with 'virtualbox' provider...
    default: The Berkshelf shelf is at "/Users/user/.berkshelf/vagrant-berkshelf/shelves/berkshelf20170427-7189-a5rhqi-default"
==> default: Sharing cookbooks with VM
==> default: Importing base box 'ubuntu/trusty64'...
...
```

This will initialize the cookbook submodule (if it doesn't already exist) and start a VirtualBox vm using the cookbook to provision it.  Most importantly, this shares the `data-lexingtonky` directory with the vm.  Any changes made to files within this directory are mirrored in the coupled OS.

### Work Flow

Once the vm is up and running, you can ssh in to activate the virtual environment and start the server:

```bash
$ cd chef-lfucg
$ vagrant ssh
...
$ source env/bin/activate
(env) $ cd cd data-lexingtonky/lfucg-ckan/
(env) $ paster serve config.ini
Starting server in PID 22790.
serving on 0.0.0.0:8000 view at http://127.0.0.1:8000
Quit the server with CONTROL-C.
```

View your site on `localhost:8000`!
