import os
import time
import glob
import json
import pickle
import requests

import _utils


def process_webhooks():
    """
        Searches for webhook files, and sends the result if completed.
    """
    # list of webhooks left to send.
    webhooks_left = glob.glob(os.path.join(_utils.RAM_DIR, "*webhook"))
    if not webhooks_left:
        return

    for webhook_f in webhooks_left:
        try:
            # check if res exists
            unique_id = os.path.basename(webhook_f).split(".")[0]
            res_path = glob.glob(os.path.join(_utils.RAM_DIR, f"{unique_id}*res"))
            if not res_path:
                continue
            res_path = res_path[0]

            try:
                pred = pickle.load(open(res_path, "rb"))
            except:
                # This means, preds are not written yet.
                continue

            try:
                json.dumps(pred)
            # if return dict has any non json serializable values, this might help.
            except:
                pred = str(pred)
            pred = {"prediction": pred, "success": True, "unique_id": unique_id}

            webhook_url = open(webhook_f).read().strip()
            # try 3 times with timeout=5 seconds.
            for _ in range(3):
                try:
                    requests.post(webhook_url, json=pred, timeout=5)
                    _utils.logger.info(f"webhook success: {unique_id}")
                    _utils.logger.info(f"{unique_id} with url {webhook_url} processed.")
                    break
                except Exception as ex:
                    _utils.logger.warn(ex)
                    _utils.logger.warn(
                        f"webhook failed for {unique_id} with url {webhook_url} in try {_}"
                    )
                    pass

            # will be deleted after success or after 3 fails
            _utils.cleanup(unique_id)
        except Exception as exc:
            try:
                unique_id = os.path.basename(webhook_f).split(".")[0]
                _utils.cleanup(unique_id)
            except Exception as exx:
                _utils.logger.warn(exx, exc_info=True)
                _utils.logger.warn(f"Failed to cleanup {webhook_f}")

            _utils.logger.exception(exc, exc_info=True)


def remove_older_files():
    os.system(
        f"find {_utils.DISK_DIR} -mindepth 1 -not -newermt '-{_utils.DELETE_OLDER_THAN} seconds' -delete"
    )
    os.system(
        f"find {_utils.RAM_DIR} -mindepth 1 -not -newermt '-{_utils.DELETE_OLDER_THAN} seconds' -delete"
    )


while True:
    # This is the loop where non cpu heavy, managerial stuff happens.
    #
    process_webhooks()

    time.sleep(_utils.MANAGER_LOOP_SLEEP)
