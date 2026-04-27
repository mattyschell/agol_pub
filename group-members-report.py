import argparse
import sys

import organization


def main():

    parser = argparse.ArgumentParser(
        description='Write an ArcGIS Online group membership report to text'
    )
    parser.add_argument('groupid'
                       ,help='ArcGIS Online group id')
    parser.add_argument('outfile'
                       ,help='Output text file path')
    parser.add_argument('--url'
                       ,default='https://nyc.maps.arcgis.com/'
                       ,help='ArcGIS Online organization url')
    args = parser.parse_args()

    try:
        org = organization.Organization.from_env(args.url)
        reporter = organization.GroupReporter(org)
        report = reporter.group_members_report(args.groupid)
        reporter.write_report_text(report
                                  ,args.outfile)
    except Exception as e:
        raise ValueError(
            'Failure writing group report for {0}: {1}'.format(
                args.groupid
               ,e))

    sys.exit(0)


if __name__ == '__main__':
    main()
