#!/bin/bash

set -e

CODE_DIR="$( cd "$( dirname "${LAUNCHFILE}" )" >/dev/null 2>&1 && pwd )"

# YOUR CODE BELOW THIS LINE
# ----------------------------------------------------------------------------

# adding services
echo "Activating services broadcast..."
robot_type="unknown"
robot_type_file="/data/stats/init_sd_card/parameters/robot_type"
service_file="${CODE_DIR}/avahi-services/dt.online.service"
service_name=$(basename -- "${service_file}")
install_service_file="${avahi_services_dir}/${service_name}"
avahi_services_dir="/etc/avahi/services"
if [ -f "${robot_type_file}" ]; then
  robot_type=$(cat "${robot_type_file}")
else
  echo "WARNING: Robot type not found in '${robot_type_file}'. Broadcasting type=unknown."
fi
sed "s/DT_ROBOT_TYPE/${robot_type}/g" "${service_file}" > "${install_service_file}"
echo "Done!"
echo ""

# launching app
echo "> Launching process..."
python3 -m "dt_broadcaster.main"
echo "< Process terminated with exit code ${$?}"

# removing services
echo ""
echo "Deactivating services broadcast..."
rm -f "${install_service_file}"
echo "Done!"
