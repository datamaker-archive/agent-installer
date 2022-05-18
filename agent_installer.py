from contextlib import contextmanager

import os
import subprocess

from pathlib import Path

from config_file import config
import re

#@contextmanager
#def virtualenv():
#    """A context manager for executing commands within the context of a
#    Python virtualenv.
#
#    >>> with virtualenv():
#    ...     print(local.python("-c", "import sys;
#                               print(sys.executable)"))
#    ... #...
#
#    """
#    virtualenv_dir = f"{config['workspace']}/datamaker-agent/.venv"
#
#    old_path = local.env['PATH']
#    virtualenv_bin_dir = (Path(virtualenv_dir) / 'bin').resolve()
#    new_path = '{}:{}'.format(str(virtualenv_bin_dir), old_path)
#    local.env['PATH'] = new_path
#    old_python = local.python
#    new_python = local['python']
#    local.python = new_python
#    try:
#        yield
#    finally:
#        local.env['PATH'] = old_path
#        local.python = old_python

class INSTALL_CUDA:
    def __init__(self):
#        self.root_password = config['root_password']
        self.agent_password = config['agent_password']
        self.set_python_version = config['set_python_version']
        self.agent_home = config['agent_home']
        self.workspace = f'{self.agent_home}/datamaker-agent'
        self.domain = config['domain']

        self.WORKSPACE_CODE = config['WORKSPACE_CODE']
        self.BACKEND_HOST = config['BACKEND_HOST']
        self.TEMP_ROOT = config['TEMP_ROOT']
        self.EXPORT_ROOT = config['EXPORT_ROOT']
        self.AGENT_ID = config['AGENT_ID']
        self.TOKEN = config['TOKEN']

        self.current_run_level = subprocess.check_output("who -r | awk '{print $2}'", shell=True).decode('utf-8')
        self.current_python_version = subprocess.check_output("python3 --version | awk '{print $2}'", shell=True).decode('utf-8')[0:3]
        self.current_deploy = subprocess.check_output(f'echo "{self.agent_password}" | sudo -S cat /etc/passwd | sed -n "/agent:/p"', shell=True).decode('utf-8')
        self.current_deploy_yn = "y" if len(str(self.current_deploy)) > 0 else "n"
        self.current_os_version_char = subprocess.check_output("grep . /etc/*-release | grep -Ei 'Ubuntu (18|20){1}' | sed -r 's/.*Ubuntu (18|20){1}.*/\\1/g'", shell=True).decode('utf-8')[0:2]
        self.current_os_version_check = str(self.current_os_version_char) if len(str(self.current_os_version_char)) > 0 else 'None'

    def previous_job(self):
        os.system('apt update -y')
        os.system('apt install -y python3-pip')
        os.system('pip3 install plumbum')
        __import__('plumbum', fromlist=['local'])

    @contextmanager
    def set_workspace(self):
        oldpwd=os.getcwd()
        os.chdir(self.agent_home)
        try:
            yield
        finally:
            os.chdir(oldpwd)

    def create_account(self):
        print('user_add')
        os.system(f'useradd -s /bin/bash -m agent')
        os.system(f'echo "agent:{self.agent_password}" | chpasswd')
        os.system('usermod -aG sudo,www-data agent')

    def change_runlevel(self, param):
        os.system(f'init {param}')

    def change_python_version(self):
        print(self.current_python_version)
        if Path('/usr/local/bin/pip').is_file()==True and Path('/usr/bin/pip').is_file()==True:
            os.system('apt-get install python3-distutils')
            os.system('curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py')
            os.system('python3 get-pip.py')

        if float(self.current_python_version) < 3.8:
            os.system('apt-get install -y python3.8 python3.8-dev')
            os.system('update-alternatives --install /usr/bin/python python /usr/bin/python3.8 2')
            os.system('update-alternatives --install /usr/bin/python python /usr/bin/python3.6 1')
            os.system('update-alternatives --auto python')

            os.system('update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 2')
            os.system('update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.6 1')
            os.system('update-alternatives --auto python3')
        else:
            print('Satisfied Python version')

    def uninstall_cuda(self):
#        os.system('cuda-uninstaller')
        os.system('/usr/local/cuda/bin/cuda-uninstaller')

    def uninstall_nvidia(self):
        os.system('nvidia-uninstall -s')

    def install_cuda_and_nvidia(self):
        print('install cuda&nvidia driver')
        # cuda wget yn
        cuda = subprocess.check_output('ls | grep -i cuda_11 | wc -w', shell=True).decode('utf-8')
        if int(cuda) > 0:
            print('Already downloaded cuda')
        else:
            print('start download cuda')

            if self.current_os_version_check == '18':
                os.system('wget http://developer.download.nvidia.com/compute/cuda/11.0.2/local_installers/cuda_11.0.2_450.51.05_linux.run')
                os.system('chmod +x cuda_11.0.2_450.51.05_linux.run')

                self.uninstall_nvidia()
                self.uninstall_cuda()

                os.system('./cuda_11.0.2_450.51.05_linux.run --silent')

            elif self.current_os_version_check == '20':
                os.system('wget https://developer.download.nvidia.com/compute/cuda/11.3.0/local_installers/cuda_11.3.0_465.19.01_linux.run')
                os.system('chmod +x cuda_11.3.0_465.19.01_linux.run')

                self.uninstall_nvidia()
                self.uninstall_cuda()

                os.system('./cuda_11.3.0_465.19.01_linux.run --silent')
            else:
                print('OS version error')

    def git_pull(self):
        with self.set_workspace():
            print('git pull')
            os.system('sudo -u agent -H git clone https://gitlab+deploy-token-1013375:STuuoVwjRykr_8uNiaXB@gitlab.com/datamaker/datamaker-agent') # ml_agent git clone
            os.system(f'sudo -u agent -H cp {self.workspace}/.env.dist  {self.workspace}/.env')

            os.system(f'mkdir {self.agent_home}/datamaker-plugins')
            os.system(f'chown -R agent:agent {self.agent_home}/datamaker-plugins')

            os.system(f"sed -ri 's/(ENVIRONMENT=).+/\\1production/g' {self.workspace}/.env")
            os.system(f"sed -ri 's/(SECRET_KEY=).+/\\1jkldfjgklujte!@#$SSSFddd/g' {self.workspace}/.env")
            os.system(f"sed -ri 's/(EMAIL_URL=).+/\\1smtp+tls:\/\/no-reply%40datamaker.io:Yom81893@smtp.office365.com:587/g' {self.workspace}/.env")
            os.system(f"sed -ri 's/(DEFAULT_FROM_EMAIL=).+/\\1no-reply@datamaker.io/g' {self.workspace}/.env")
            os.system(f"sed -ri 's/(SERVER_EMAIL=).+/\\1developer@datamaker.io/g' {self.workspace}/.env")
            os.system(f"sed -ri 's/(CACHE_URL=.*)&password=.*$/\\1/g' {self.workspace}/.env")

    def install_package(self):
        if self.current_os_version_check == '18':
            os.system('apt install -y libpq-dev postgresql postgresql-contrib postgis nginx redis-server nfs-common gettext ffmpeg curl git')
            os.system('snap install --classic certbot')

        elif self.current_os_version_check == '20':
            os.system('apt install -y python3-dev libpq-dev postgresql postgresql-contrib postgis nginx redis-server nfs-common gettext ffmpeg python3-certbot-nginx curl git')

        else:
            print('OS version error')

        os.system('pip3 install --upgrade pip')
        os.system('pip3 install virtualenv')
        os.system('pip3 install fabric')

        os.system('sed -ri "/listen \[::\]/D" /etc/nginx/sites-available/default') # ipv6 disable
        os.system('systemctl start nginx.service')
        os.system("sed -ri 's/(bind 127.0.0.1) ::1/\\1/g' /etc/redis/redis.conf")
        os.system('systemctl start redis-server.service')
        os.system("systemctl enable redis-server.service")

    def set_ml_agent(self):
        os.chdir(self.workspace)
        os.system('sudo -u agent -H virtualenv .venv')

        os.system('sed -i "/torch==.*/d" requirements.txt')
        os.system('sed -i "/detectron2/d" requirements.txt')

        if self.current_os_version_check == '18':
            os.system(f'sudo -u agent -H {self.workspace}/.venv/bin/pip install torch==1.7.1+cu110 torchvision==0.8.2+cu110 torchaudio==0.7.2 -f https://download.pytorch.org/whl/torch_stable.html')
            os.system(f'sudo -u agent -H {self.workspace}/.venv/bin/pip install detectron2==0.5 -f https://dl.fbaipublicfiles.com/detectron2/wheels/cu110/torch1.7/index.html')

        elif self.current_os_version_check == '20':
            os.system(f'sudo -u agent -H {self.workspace}/.venv/bin/pip install torch==1.10.2+cu113 torchvision==0.11.3+cu113 torchaudio==0.10.2+cu113 -f https://download.pytorch.org/whl/cu113/torch_stable.html')
            os.system(f'sudo -u agent -H {self.workspace}/.venv/bin/pip install detectron2 -f https://dl.fbaipublicfiles.com/detectron2/wheels/cu113/torch1.10/index.html')
        else:
            print('OS version error')

        os.system(f'sudo -u agent -H {self.workspace}/.venv/bin/pip install --upgrade pip')
        os.system(f'sudo -u agent -H {self.workspace}/.venv/bin/pip install gunicorn numpy celery')
        os.system(f'sudo -u agent -H {self.workspace}/.venv/bin/pip install jupyterlab')
        os.system(f'sudo -u agent -H {self.workspace}/.venv/bin/pip install -r requirements.txt')
        
        os.system(f'sudo -u agent -H {self.workspace}/.venv/bin/pip install git+https://gitlab+deploy-token-1015277:StLPQzA-dA46TFHfJQgc@gitlab.com/datamaker/datamaker-sdk.git')

#        os.system(f'sudo -u agent -H {self.workspace}/.venv/bin/python manage.py makemigrations')
        os.system(f'sudo -u agent -H {self.workspace}/.venv/bin/python manage.py migrate')
        os.system(f'sudo -u agent -H {self.workspace}/.venv/bin/python manage.py collectstatic --noinput')

        os.system(f"sudo -u agent -H {self.workspace}/.venv/bin/python manage.py constance set WORKSPACE_CODE '{self.WORKSPACE_CODE}'")
        os.system(f"sudo -u agent -H {self.workspace}/.venv/bin/python manage.py constance set BACKEND_HOST '{self.BACKEND_HOST}'")
        os.system(f"sudo -u agent -H {self.workspace}/.venv/bin/python manage.py constance set TEMP_ROOT '{self.TEMP_ROOT}'")
        os.system(f"sudo -u agent -H {self.workspace}/.venv/bin/python manage.py constance set EXPORT_ROOT '{self.EXPORT_ROOT}'")
        os.system(f"sudo -u agent -H {self.workspace}/.venv/bin/python manage.py constance set AGENT_ID '{self.AGENT_ID}'")
        os.system(f"sudo -u agent -H {self.workspace}/.venv/bin/python manage.py constance set TOKEN '{self.TOKEN}'")

    def set_gunicorn(self):
        os.system('cat /dev/null > /etc/systemd/system/gunicorn.socket')
        f = open('/etc/systemd/system/gunicorn.socket', 'w')
        f.writelines('\n'.join(['[Unit]','Description=gunicorn socket', '\n','[Socket]', 'ListenStream=/run/gunicorn.sock', '\n', '[Install]', 'WantedBy=sockets.target']))
        f.close()

        os.system('cat /dev/null > /etc/systemd/system/gunicorn.service')
        f2 = open('/etc/systemd/system/gunicorn.service', 'w')
        f2.writelines('\n'.join(['[Unit]', 'Description=gunicorn daemon', 'Requires=gunicorn.socket', 'After=network.target', '\n', '[Service]', 'User=agent', 'Group=www-data', 'Environment=LANG=en_US.utf8', 'Environment=LC_ALL=en_US.UTF-8', 'Environment=LC_LANG=en_US.UTF-8' , f'WorkingDirectory={self.workspace}', f'ExecStart={self.workspace}/.venv/bin/gunicorn --access-logfile - --workers 3 --timeout 300 --bind unix:/run/gunicorn.sock agent.wsgi:application', '\n', '[Install]', 'WantedBy=multi-user.target']))
        f2.close()

        os.system('systemctl daemon-reload')
        os.system('systemctl start gunicorn.socket gunicorn.service')
        os.system('systemctl enable gunicorn.socket gunicorn.service')

    def setting_nginx(self):
        os.system('cat /dev/null > /etc/nginx/sites-available/agent')
        f = open('/etc/nginx/sites-available/agent', 'w')
        f.writelines('\n'.join(['server {', '    listen 80;', f'    server_name {self.domain};', '\n', '    location /media  {', '        alias /mnt/media/datamaker-annotator-backend-dev;', '    }', '\n', '    location /static {', f'        alias {self.workspace}/resources/static;', '    }', '\n', '    location /jupyter {', f'        proxy_pass http://localhost:8888/jupyter;', '        proxy_headers_hash_max_size 512;', '        proxy_headers_hash_bucket_size 128;', '        proxy_set_header X-Real-IP $remote_addr;', '        proxy_set_header Host $host;', '        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;', '        proxy_http_version     1.1;', '        proxy_set_header      Upgrade "websocket";', '        proxy_set_header      Connection "Upgrade";', '        proxy_read_timeout    86400;', '        proxy_buffering off;', '    }','\n','    location / {', '        include proxy_params;', '        proxy_pass http://unix:/run/gunicorn.sock;', '    }', '}']))
        f.close()
        os.system('ln -s /etc/nginx/sites-available/agent /etc/nginx/sites-enabled/agent')

    def setting_celery(self):
        os.system('mkdir -p /etc/conf.d')
        os.system('cat /dev/null > /etc/conf.d/celery')
        f = open('/etc/conf.d/celery', 'w')
        f.writelines('\n'.join(['CELERYD_NODES="w1"',f'CELERY_BIN="{self.workspace}/.venv/bin/celery"','CELERY_APP="agent"','CELERYD_MULTI="multi"','CELERYD_OPTS=""','\n','CELERYD_PID_FILE="/run/celery/%n.pid"','CELERYD_LOG_FILE="/var/log/celery/%n%I.log"','CELERYD_LOG_LEVEL="INFO"','\n','CELERYBEAT_PID_FILE="/run/celery/beat.pid"','CELERYBEAT_LOG_FILE="/var/log/celery/beat.log"']))
        f.close()
        os.system('cat /dev/null > /etc/systemd/system/celery.service')
        f2 = open('/etc/systemd/system/celery.service', 'w')
        f2.writelines('\n'.join(["[Unit]","Description=Celery Service","After=network.target","\n","[Service]","Type=forking","User=agent","Group=www-data","EnvironmentFile=/etc/conf.d/celery",f"WorkingDirectory={self.workspace}","ExecStart=/bin/sh -c '${CELERY_BIN} ${CELERYD_MULTI} start ${CELERYD_NODES} -A ${CELERY_APP} --pidfile=${CELERYD_PID_FILE} --logfile=${CELERYD_LOG_FILE} --loglevel=${CELERYD_LOG_LEVEL} ${CELERYD_OPTS}'","ExecStop=/bin/sh -c '${CELERY_BIN} ${CELERYD_MULTI} stopwait ${CELERYD_NODES} --pidfile=${CELERYD_PID_FILE}'","ExecReload=/bin/sh -c '${CELERY_BIN} ${CELERYD_MULTI} restart ${CELERYD_NODES} -A ${CELERY_APP} --pidfile=${CELERYD_PID_FILE} --logfile=${CELERYD_LOG_FILE} --loglevel=${CELERYD_LOG_LEVEL} ${CELERYD_OPTS}'""\n","[Install]","WantedBy=multi-user.target"]))
        f2.close()
        os.system('cat /dev/null > /etc/tmpfiles.d/celery.conf')
        f3 = open('/etc/tmpfiles.d/celery.conf', 'w')
        f3.writelines('\n'.join(['d /run/celery 0755 agent www-data -','d /var/log/celery 0755 agent www-data -']))
        f3.close()
        os.system('systemd-tmpfiles --create')
        os.system('systemctl daemon-reload')
        os.system('systemctl restart celery')
        os.system('systemctl enable celery')

    def setting_jupyter(self):
        os.system(f'mkdir {self.agent_home}/notbooks')
        notebook_password = subprocess.check_output(f"export j_random_salt=\"$(tr -dc a-f0-9 < /dev/urandom | head -c 12)\"; printf \"$(echo '{self.agent_password}' | iconv -t utf-8)$j_random_salt\" | sha1sum | awk -v alg=\"sha1\" -v salt=$j_random_salt '{{print alg \":\" salt \":\" $1}}'; unset j_random_salt", shell=True).decode('utf-8').replace("\n", "")
        
        os.system('cat /etc/null > /etc/systemd/system/jupyterlab.service')
        f1 = open('/etc/systemd/system/jupyterlab.service', 'w')
        f1.writelines('\n'.join(["[Unit]", "Description=Jupyter Notebook", "\n", "[Service]", "Type=simple", "PIDFile=/run/jupyter.pid", f"ExecStart={self.workspace}/.venv/bin/jupyter-lab --notebook-dir={self.agent_home}/notbooks/ --ip='*' --port=8888 --no-browser --LabApp.base_url=/jupyter --NotebookApp.base_url=/jupyter --NotebookApp.password='{notebook_password}'", "User=agent", "Group=www-data", "Restart=always", "RestartSec=10", "\n", "[Install]", "WantedBy=multi-user.target"]))
        f1.close()

        os.system('systemctl daemon-reload')
        os.system('systemctl enable jupyterlab.service')
        os.system('systemctl start jupyterlab.service')

    def install_all(self):
        self.previous_job()
        self.create_account()

        if int(self.current_run_level) == 5:
            self.change_runlevel('3')
            print('RUN LEVEL - 5')
        elif int(self.current_run_level) == 3:
            print('RUN LEVEL - 3')
        else:
            print('RUN LEVEL - ERROR')
            exit()

        self.change_python_version()
        self.install_cuda_and_nvidia()
        self.install_package()
        self.git_pull()
        self.set_ml_agent()
        self.set_gunicorn()
        self.setting_nginx()
        self.setting_celery()
        self.setting_jupyter()

        os.system('reboot')

    def check_enviroment(self):
        print('_____________________INFO START_________________________')
        print(f'CURRENT RUN LEVEL - {self.current_run_level}')
        print(f'SET PYTHON VERSION - {self.current_python_version}')
        print(f'SET domain - {self.domain}')
        print(f'SET agent_home  - {self.agent_home}')
        print(f'SET workspace - {self.workspace}')
        print('_______________________INFO END_________________________')

        #Check support OS
        if self.current_os_version_check == '20' or self.current_os_version_check == '18':
            print('Okay - Support OS')
        else:
            print('Sorry. Not Support OS.. Agent support Ubuntu 18.xx.x and Ubuntu 20.xx.x')
            exit()

        chk_domain_p = re.compile("^([a-z0-9\w]+\.*)+[a-z0-9]{2,4}$")
        chk_domain_m = chk_domain_p.match(self.domain)
        chk_domain2_p = re.compile("^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$")
        chk_domain2_m = chk_domain2_p.match(self.domain)
        if chk_domain_m or chk_domain2_m:
            print('Okay - set domain ')
        else:
            print('In config_file.py Domain is wrong... Edit config_file.py.. ex): xxx.xxx.com ')
            exit()

        chk_agent_home_p = re.compile("^/home/[a-z_-]+$")
        chk_agent_home_m = chk_agent_home_p.match(self.agent_home)

        if chk_agent_home_m:
            print('OKAY - set agent_home')
        else:
            print('In config_file.py agent_home is wrong... Edit Config_file.py.. ex): /home/{your home}')
            exit()

        chk_agent_workspace_p = re.compile("^/home/[a-z]+/datamaker-agent$")
        chk_agent_workspace_m = chk_agent_workspace_p.match(self.workspace)

        if chk_agent_workspace_m:
            print('OKAY - set agent_home')
        else:
            print('In config_file.py agent_workspace is wrong... Edit Config_file.py.. ex): /home/{your home}/datamaker-agent')
            exit()

        chk_workspace_code_p = re.compile("^\w{40}$")
        chk_workspace_code_m = chk_workspace_code_p.match(self.WORKSPACE_CODE)

        if chk_workspace_code_m:
            print('OKAY - set workspace_code')
        else:
            print('In config_file.py workspace_code is wrong... Edit Config_file.py.. Enter the issued code')
            exit()

        chk_backend_host_p = re.compile("^https://([a-z0-9\w]+\.*)+[a-z0-9]{2,4}")
        chk_backend_host_m = chk_backend_host_p.match(self.BACKEND_HOST)

        if chk_backend_host_m:
            print('OKAY - set backend_host')
        else:
            print('In config_file.py backend_code is wrong... Edit Config_file.py.. Enter the issued backend_host')
            exit()

        chk_agent_id_p = re.compile("^[0-9]+$")
        chk_agent_id_m = chk_agent_id_p.match(self.AGENT_ID)

        if chk_agent_id_m:
            print('OKAY - set agent_id')
        else:
            print('In config_file.py agent_id is wrong... Edit Config_file.py.. Enter the issued agent_id')
            exit()

        chk_token_p = re.compile("^\w{40}$")
        chk_token_m = chk_token_p.match(self.TOKEN)

        if chk_token_m:
            print('OKAY - set token')
        else:
            print('In config_file.py token is wrong... Edit Config_file.py.. Enter the issued token')
            exit()

ins_cuda = INSTALL_CUDA()
ins_cuda.check_enviroment()
ins_cuda.install_all()
