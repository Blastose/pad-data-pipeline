#!/usr/bin/env bash
#
# Updates the local cache of full monster pics / portraits from the JP server.

cd "$(dirname "$0")" || exit
source ../shared_root.sh
source ../shared.sh
source ../discord.sh
source "${VENV_ROOT}/bin/activate"

function error_exit() {
  hook_error "Image Pipeline failed <@&${NOTIFICATION_DISCORD_ROLE_ID}>"
  hook_file "/tmp/dg_image_log.txt"
}

function success_exit() {
  echo "Image pipeline finished"
  hook_info "Image pipeline finished"
}

# Enable alerting to discord
trap error_exit ERR
trap success_exit EXIT

RUN_DIR="${MEDIA_ETL_DIR}/image_pull"

# Enable NVM (Spammy)
set +x
export NVM_DIR="$([ -z "${XDG_CONFIG_HOME-}" ] && printf %s "${HOME}/.nvm" || printf %s "${XDG_CONFIG_HOME}/nvm")"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm use 8
set -x

yarn --cwd=${PAD_RESOURCES_ROOT} update

# Full pictures
python3 "${RUN_DIR}/PADTextureDownload.py" \
  --output_dir="${IMG_DIR}/na/full" \
  --server=NA

python3 "${RUN_DIR}/PADAnimatedGenerator.py" \
  --raw_dir="${IMG_DIR}/na/full/raw_data" \
  --working_dir="${PAD_RESOURCES_ROOT}" \
  --output_dir="${IMG_DIR}/na/full/corrected_data"

python3 "${RUN_DIR}/PADTextureDownload.py" \
  --output_dir="${IMG_DIR}/jp/full" \
  --server=JP

python3 "${RUN_DIR}/PADAnimatedGenerator.py" \
  --raw_dir="${IMG_DIR}/jp/full/raw_data" \
  --working_dir="${PAD_RESOURCES_ROOT}" \
  --output_dir="${IMG_DIR}/jp/full/corrected_data"

# Portraits
python3 ${RUN_DIR}/PADPortraitsGenerator.py \
  --input_dir="${IMG_DIR}/na/full/extract_data" \
  --data_dir="${RAW_DIR}" \
  --card_templates_file="${RUN_DIR}/wide_cards.png" \
  --server=na \
  --output_dir="${IMG_DIR}/na/portrait/local"

python3 ${RUN_DIR}/PADPortraitsGenerator.py \
  --input_dir="${IMG_DIR}/jp/full/extract_data" \
  --data_dir="${RAW_DIR}" \
  --card_templates_file="${RUN_DIR}/wide_cards.png" \
  --server=jp \
  --output_dir="${IMG_DIR}/jp/portrait/local"

# Animations
python3 "${RUN_DIR}/PADAnimationGenerator.py" \
  --raw_dir="${IMG_DIR}/jp/full/raw_data" \
  --working_dir="${PAD_RESOURCES_ROOT}" \
  --output_dir="${IMG_DIR}/animated"

# Force a sync
${CRONJOBS_DIR}/sync_data.sh
