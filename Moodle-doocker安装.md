


Would you like to learn how to install Moodle using Docker on Ubuntu Linux? In this tutorial, we are going to show you all the steps required to perform the Moodle installation using Docker on a computer running Ubuntu Linux in 5 minutes or less.
• Ubuntu 20.04
• Moodle 3.10.3
• MariaDB 10.5.5
 

# Tutorial Moodle – Docker Installation

#### Install the Docker service.

* apt-get update
* apt-get install docker.io

#### 创建Docker网络

* docker network create moodle-network

#### 下载数据库镜像

* docker pull mariadb

#### 下载moodle镜像

* docker pull bitnami/moodle

查看下载的镜像：
* docker images
应该能看到mariadb和moodle两个image。
#### Create a docker volume to store the MariaDB persistent data.

* docker volume create mariadb-data

##### Verify the persistent data directory.

* docker volume inspect mariadb-data



##### Optionally, create a symbolic link to an easier access location.

1
ln -s /var/lib/docker/volumes/mariadb-data/_data /mariadb
#### Start a MariaDB container with persistent data storage.

1
* docker run -d --name moodledb -v mariadb-data:/var/lib/mysql --network moodle-network -e "MYSQL_ROOT_PASSWORD=ray621112" -e MYSQL_USER=moodle -e "MYSQL_PASSWORD=ray621112" -e "MYSQL_DATABASE=moodle" mariadb

The database ROOT account password configured was ray621112.
A database named Moodle was created.
A database account named Moodle was created and the password kamisama123 was configured.



### 保存用户数据，Create a docker volume to store Moodle persistent data.
* docker volume create moodle-data
Verify the persistent data directory.

1
* docker volume inspect moodle-data
Here is the command output:

Optionally, create a symbolic link to an easier access location.

1
* ln -s /var/lib/docker/volumes/moodle-data/_data /moodle
Start a Moodle container with persistent data storage.

1
* docker run -d --name moodle -p 8090:8080 -p 8443:8443 -v moodle-data:/bitnami/moodle --network moodle-network -e MOODLE_DATABASE_HOST=moodledb -e MOODLE_DATABASE_USER=moodle -e MOODLE_DATABASE_PASSWORD=ray621112 -e MOODLE_DATABASE_NAME=moodle bitnami/moodle:latest

如果发现容器名已经占用，可以用docker volume rm 删除命名容器

It may take up to 5 minutes for Moodle to finish the installation process.
 
 

### 在浏览器中设置
Open your browser and enter the IP address of your web server.
In our example, the following URL was entered in the Browser:
• http://10.8.116.47:8090/
The Moodle web interface should be presented, click on the Login option.
On the prompt screen, enter the following information.
• Username: user
• Password: bitnami
After a successful login, the Moodle dashboard will be displayed.

Congratulations! You have finished the Moodle Docker installation.
 
 登录之后可以修改语言界面等各种相关选项。
 
 


### Tutorial Moodle – Docker container management
Verify the status of all Docker containers using the following command:


docker ps -a
Verify the status of a container.

1
docker ps -a -f name=moodle
2
docker ps -a -f name=moodledb
To stop a container, use the following command:

1
docker container stop moodle
2
docker container stop moodledb
To start a container, use the following command:

1
docker container start moodle
2
docker container start moodledb
To restart a container, use the following command:

1
docker container restart moodle
2
docker container restart moodledb
In case of error, use the following command to verify the container logs.

1
docker logs moodle
2
docker logs moodledb
In our examples, we demonstrated how to manage Moodle containers.


## 安装简体中文

Moodle系统是一个开源的系统，采用PHP CLI安装后默认是英语界面，本文将介绍安装中文语言包，设置中文界面的方法。
 1.安装简体中文语言包
英文界面下，管理员登录，点击【Site administration】——【language】—【language packs】;
 在右侧的【available language packs】中，滚动条到最底部，选中【简体中文zh_cn】;
最后，右下角按钮【install selected language pack（s）】


## jobe 的docker安装

git clone https://github.com/haharay/jobeinabox.git
cd jobeinabox
docker build . -t my/jobeinabox --build-arg TZ="Asia/Shanghai"
运行在8087端口：
docker run -d -p 8087:80 --name jobe my/jobeinabox
测试：会返回语言版本的json
http://10.8.116.47:8087/jobe/index.php/restapi/languages
只需设置coderuner插件的服务器为：10.8.116.47:8087，并去掉密码既可以。

## Docker Volume的备份与恢复


## 
用户 ：hcmray,12),为系统管理员
  he;12)为全部具有课程管理、课程创建角色的教师。