import paramiko
import os

def lambda_handler(event, context):
    # === Configuration ===
    ec2_host = "75.101.248.64"  # EC2 Public IP or DNS
    ec2_user = "ec2-user"  # or 'ubuntu'
    ansible_playbook = "/etc/ansible/deploy.yaml"
    key_file_path = "/var/task/ansible.pem"  # path inside Lambda deployment package

    # Make sure permissions are correct (Lambda needs read-only for key)
    #os.chmod(key_file_path, 0o400)

    # === Load OpenSSH key ===
    try:
        try:
            # Try RSA key
            pkey = paramiko.RSAKey.from_private_key_file(key_file_path)
        except paramiko.ssh_exception.SSHException:
            try:
                # Try Ed25519
                pkey = paramiko.Ed25519Key.from_private_key_file(key_file_path)
            except Exception:
                # Try ECDSA as fallback
                pkey = paramiko.ECDSAKey.from_private_key_file(key_file_path)
    except Exception as e:
        print(f" Failed to load private key: {e}")
        raise

    # === SSH Connection ===
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh_client.connect(hostname=ec2_host, username=ec2_user, pkey=pkey)
        print(f" Connected to {ec2_host}")

        # === Run your Ansible playbook ===
        command = f"ansible-playbook {ansible_playbook}"
        stdin, stdout, stderr = ssh_client.exec_command(command)

        print(" STDOUT:\n", stdout.read().decode())
        print(" STDERR:\n", stderr.read().decode())

    except Exception as e:
        print(f" SSH or command execution failed: {e}")
        raise
    finally:
        ssh_client.close()
        print(" SSH connection closed.")
