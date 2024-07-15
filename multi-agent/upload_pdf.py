import paramiko

class SSHManager:
    def __init__(self, host, port, username, password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    def connect(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(self.host, port=self.port, username=self.username, password=self.password)
        

    def upload_file(self, local_path, remote_path):
        ftp_client = self.client.open_sftp()
        ftp_client.put(local_path, remote_path)
        ftp_client.close()

    def download_file(self, remote_path, local_path):
        ftp_client = self.client.open_sftp()
        ftp_client.get(remote_path, local_path)
        ftp_client.close()

    def execute_command(self, command):
        stdin, stdout, stderr = self.client.exec_command(command)
        exit_status = None

        try:
            # 等待命令执行完成
            exit_status = stdin.channel.recv_exit_status()

            # 打印命令执行结果
            print("命令执行结果：")
            for line in stdout:
                print(line.strip())

            # 打印错误信息（如果有）
            for line in stderr:
                print(line.strip(), "错误")

            # 根据退出状态码判断命令是否成功执行
            if exit_status == 0:
                print("Command finish")
            else:
                print("Command Fail，exit code ：", exit_status)
        except Exception as e:
            print("Fail : ", e)

    def close(self):
        self.client.close()

    def run(self,filename,local_path,remote_path="./RAG_main/"):
        self.connect()
        self.upload_file(local_path,remote_path+filename)
        # self.execute_command("ls")


# 连接参数
host = "region-9.autodl.pro"
port = 53208 
username = "root"
password = "4VJLWZNRq4v2"

# 实例化 SSHManager
ssh_manager = SSHManager(host, port, username, password)

# 连接到远程服务器
ssh_manager.connect()

# 执行命令
command = "ls"
# ssh_manager.execute_command(command)
# ssh_manager.upload_file(filename="applefinancialfile.md",local_path="./readme.md")

# 关闭连接
ssh_manager.close()
