"""Independent validator on CV1 separately frozen retry; original source retained."""
import argparse
import cross_visit_map_pilot_attempt02 as retry
import validate_cross_visit_map_pilot as validator

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage',choices=('bank','evaluate'))
    stage = parser.parse_args().stage
    retry.run.record_stage('validate_'+stage,getattr(validator,stage))
