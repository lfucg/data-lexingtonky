lock '3.1.0'

set :application, 'ckan-2.0'
set :repo_url, 'git@github.com:lfucg/data-lexingtonky.git'
set :branch, 'ckan-2.0'
set :ssh_options, {forward_agent: true}
set :deploy_to, '/home/ubuntu/data-lexingtonky-deployed'
set :deploy_via, :remote_cache

namespace :deploy do

  desc 'Restart application'
  task :restart do
    on roles(:app), in: :sequence, wait: 5 do
    end
  end

  after :publishing, :restart

  after :restart, :clear_cache do
    on roles(:web), in: :groups, limit: 3, wait: 10 do
    end
  end

end
