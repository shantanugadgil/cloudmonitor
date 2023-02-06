#!/bin/bash

set -u
set -x

# TODO: configuration to be able to choose specific regions for specific accounts

me=$(readlink -m "$0")
me_dir=$(dirname $me)

echo "[${me_dir}]"
cd "${me_dir}" || { echo "unable to chdir"; exit 1; }

account_list=${ACCOUNT_LIST:="myaccount1 myaccount2"}
region_list=${REGION_LIST:="us-east-2 us-east-1 us-west-1 us-west-2 ap-south-1 ap-northeast-2 ap-southeast-1 ap-southeast-2 ap-northeast-1 ca-central-1 eu-central-1 eu-west-1 eu-west-2 eu-west-3 eu-north-1 sa-east-1"}

base_log_dir="data"
cur_date=$(date +"%F-%H-%M-%S")

base_data_dir="${base_log_dir}/${cur_date}"

for account in $account_list; do
	for region in $region_list; do
		out_dir="${base_data_dir}/${account}/${region}"
		mkdir -p "${out_dir}"

		fname_instances="${out_dir}/instances.json"
		fname_images="${out_dir}/images.json"

		aws ec2 --profile "${account}" --region "${region}" describe-instances > "${fname_instances}"
		cat "${fname_instances}" | jq -r '.Reservations[].Instances[].ImageId' | sort -u | tr '\n' ' ' > ami_list.txt

		aws ec2 --profile "${account}" --region "${region}" describe-images describe-images --image-ids "$(cat ami_list.txt)" > "${fname_images}"
		#aws ec2 --profile "${account}" --region "${region}" describe-images --owners self > ${fname_images} &
		wait
		sleep 2
	done
done

python html_gen.py --account foo --data-dir ${base_data_dir} --outfile /tmp/index.html
sudo mv -fv /tmp/index.html /var/www/html/index.html
echo "Done"
