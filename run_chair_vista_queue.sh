#!/usr/bin/env bash
# Run the three VISTA CHAIR decoding experiments serially on one GPU.
# It can be started while the greedy run is already in progress: the script
# waits until its JSONL has 500 lines before starting beam search.

set -Eeuo pipefail

readonly PROJECT_DIR="/workspace/VISTA"
readonly PYTHON_BIN="/workspace/miniconda3/envs/vista/bin/python"
readonly GPU_ID="0"
readonly DATA_PATH="/workspace/data/coco/val2014"
readonly EXP_FOLDER="chair_three_decode"
readonly MODEL="llava-1.5"
readonly SUBSET_SIZE="500"
readonly SEED="1994"
readonly POLL_SECONDS="30"

readonly RESULT_DIR="${PROJECT_DIR}/exp_results/${EXP_FOLDER}/${MODEL}"
readonly LOG_DIR="${RESULT_DIR}/logs"
readonly COMMON_FILE_PREFIX="seed${SEED}_vsv_lambda_0.17_logaug_loglayer_25,30_logalpha_0.3"

readonly GREEDY_FILE="${RESULT_DIR}/${COMMON_FILE_PREFIX}_greedy_max_new_tokens_512.jsonl"
readonly BEAM_FILE="${RESULT_DIR}/${COMMON_FILE_PREFIX}_beam5_max_new_tokens_512.jsonl"
readonly NUCLEUS_FILE="${RESULT_DIR}/${COMMON_FILE_PREFIX}_nucleus_0.9_max_new_tokens_512.jsonl"

mkdir -p "${LOG_DIR}"
cd "${PROJECT_DIR}"

line_count() {
    local file="$1"
    if [[ -f "${file}" ]]; then
        wc -l < "${file}" | tr -d ' '
    else
        printf '0'
    fi
}

is_complete() {
    local file="$1"
    [[ "$(line_count "${file}")" -eq "${SUBSET_SIZE}" ]]
}

wait_for_existing_run() {
    local label="$1"
    local result_file="$2"

    printf '[%s] Waiting for %s: %s\n' "$(date '+%F %T')" "${label}" "${result_file}"
    while ! is_complete "${result_file}"; do
        printf '[%s] %s progress: %s/%s images\n' \
            "$(date '+%F %T')" "${label}" "$(line_count "${result_file}")" "${SUBSET_SIZE}"
        sleep "${POLL_SECONDS}"
    done
    printf '[%s] %s complete.\n' "$(date '+%F %T')" "${label}"
}

run_experiment() {
    local label="$1"
    local result_file="$2"
    shift 2

    if is_complete "${result_file}"; then
        printf '[%s] %s already complete; skipping.\n' "$(date '+%F %T')" "${label}"
        return
    fi

    if [[ -e "${result_file}" ]]; then
        printf '%s\n' "Refusing to overwrite incomplete result: ${result_file}" >&2
        printf '%s\n' 'Remove or rename that file only after confirming the interrupted run is no longer needed.' >&2
        exit 1
    fi

    printf '[%s] Starting %s. Log: %s\n' \
        "$(date '+%F %T')" "${label}" "${LOG_DIR}/${label}.log"
    CUDA_VISIBLE_DEVICES="${GPU_ID}" "${PYTHON_BIN}" chair_eval.py \
        --exp_folder "${EXP_FOLDER}" \
        --model "${MODEL}" \
        --data-path "${DATA_PATH}" \
        --subset-size "${SUBSET_SIZE}" \
        --seed "${SEED}" \
        --vsv \
        --vsv-lambda 0.17 \
        --logits-aug \
        --logits-alpha 0.3 \
        "$@" 2>&1 | tee "${LOG_DIR}/${label}.log"

    if ! is_complete "${result_file}"; then
        printf '%s\n' "${label} exited without producing ${SUBSET_SIZE} results." >&2
        exit 1
    fi
}

# Greedy is already running. This waits rather than launching a duplicate.
wait_for_existing_run "vista_greedy" "${GREEDY_FILE}"
run_experiment "vista_beam5" "${BEAM_FILE}" --num-beams 5
run_experiment "vista_nucleus_p0.9" "${NUCLEUS_FILE}" --do-sample --top-p 0.9

printf '[%s] All three VISTA decode experiments are complete.\n' "$(date '+%F %T')"
