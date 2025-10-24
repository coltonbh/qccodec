import subprocess

from qccodec.codec import decode


def test_cli(test_data_dir):
    # Call CLI script as a subprocess
    filepath = test_data_dir / "terachem" / "water.energy.out"
    sp_proc = subprocess.run(
        ["qccodec", "terachem", "energy", filepath], capture_output=True, text=True
    )
    # Check the return code
    assert sp_proc.returncode == 0

    # Check the output
    parse_data = decode("terachem", "energy", stdout=filepath.read_text())
    expected_output = parse_data.model_dump_json(
        indent=4, exclude_unset=True, exclude_defaults=True
    )
    assert sp_proc.stdout.strip() == expected_output
