set :stage, :vagrant

vagrant_port = ENV['VAGRANT_PORT'] || '2222'
set :vagrant_port, vagrant_port

vagrant_key = "#{ENV['HOME']}/.vagrant.d/insecure_private_key"
set :vagrant_key, vagrant_key

server 'localhost', user: 'ubuntu', roles: 'web',
  port: fetch(:vagrant_port),
  ssh_options: {
    keys: fetch(:vagrant_key),
    forward_agent: 'yes'
  }
