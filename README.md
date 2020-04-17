# scheduled_ec2_instance_token_renewer
Simple script that fetches EC2 Role Credentials from Instance Metadata, store them in a file and updates them before expiry

# Usage
a. Install pip

b. Run pip install -r requirements.txt

c. Run  python main.py <file_loc>

where <file_loc> is the absolute path where you intend to save you EC2 Metadata Role Credentials

# Operation
This works on an EC2 Instance configured with an appropriate role.
The credentials will only work with EC2 Services within the limits of the prescribed role. 
