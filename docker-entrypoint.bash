#!/bin/bash

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

set -u
set -e

exec 2>&1

log()
{
    local msg="$@"
    local dd=$(date +"%F-%H-%M-%S")

    echo "[$dd] $msg"
}

### script begins here ###

me=$(readlink -f "$0")
me_dir=$(dirname $me)

log "me [$me] me_dir [$me_dir]"

cd $me_dir || { echo "unable to chdir to [$me_dir] "; sleep 180; exit 1; }

### you need to map in the file ~/.aws/config with the correct "profile" settings per account

AWS_ACCOUNT_LIST=${AWS_ACCOUNT_LIST:-"undefined"}

log "AWS_ACCOUNT_LIST [$AWS_ACCOUNT_LIST]"

AWS_REGION_LIST=${AWS_REGION_LIST:-"all"}

if [[ "$AWS_REGION_LIST" == "all" ]]; then
    AWS_REGION_LIST=$(aws ec2 --region us-west-2 describe-regions | jq -r '.Regions[].RegionName' | xargs)
fi

log "AWS_REGION_LIST [$AWS_REGION_LIST]"

DELAY=${DELAY:-"300"}

log "DELAY [$DELAY]"

OUTPUT_DIR="/data"

log "OUTPUT_DIR [$OUTPUT_DIR]"

tar oxmf html.tar.xz --strip=1 -C /data

log_base_dir="/logs"

while (( 1 )); do
    cur_date=$(date +"%F-%H-%M-%S")

    base_data_dir="${log_base_dir}/${cur_date}"

    for account in ${AWS_ACCOUNT_LIST}; do

        for region in ${AWS_REGION_LIST}; do

            out_dir="${base_data_dir}/${account}/${region}"

            mkdir -pv ${out_dir}

            fname_instances="${out_dir}/instances.json"

            fname_images="${out_dir}/images.json"

            # parallelize the fetches
            aws ec2 --profile $account --region $region describe-instances > ${fname_instances} &

            aws ec2 --profile $account --region $region describe-images --owners self > ${fname_images} &

            wait

            sync

        done
    done

    python /generate_html.py --data-dir ${base_data_dir} --outfile ${OUTPUT_DIR}/index.html

    log "Sleeping [$DELAY] ..."
    sleep $DELAY
done

log "ERROR: YOU SHOULD NEVER SEE THIS MESSAGE"
sleep 10
exit 1
