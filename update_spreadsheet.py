import gspread
from oauth2client.service_account import ServiceAccountCredentials


def get_current_balance():
    from influxdb import InfluxDBClient, DataFrameClient
    import config

    client = DataFrameClient(config.influx_host, 8086, config.influxdb_user, config.influxdb_pass, 'balance_history')
    query = 'select time, BuyingPower, Cash, MarginBalance, NetLiq from balance group by * order by time desc limit 1'
    results = client.query(query)

    return results['balance']['NetLiq'].iloc[0]


def update_spreadsheet(balance):
    # define the scope
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']

    # add credentials to the account
    creds = ServiceAccountCredentials.from_json_keyfile_name('/home/sstoveld/stonks-only-go-up/portfolio-update-3ef72f62cf31.json', scope)

    # authorize the clientsheet
    client = gspread.authorize(creds)

    # get the instance of the Spreadsheet
    sheet = client.open('Trade and Portfolio Tracking')

    # get the first sheet of the Spreadsheet
    sheet_instance = sheet.get_worksheet(5)

    last_row_num = len(sheet_instance.get_all_values())
    last_row_list = sheet_instance.row_values(last_row_num, value_render_option='FORMULA')
    print(last_row_list)

    values = [
        f'=WORKDAY.INTL($A$2,row(A{last_row_num - 1}),1)',
        balance,
        f'=if(B{last_row_num + 1}<>"",(B{last_row_num + 1}-E{last_row_num + 1})/B{last_row_num}-1,"")',
        f'=if(B{last_row_num + 1}<>"",(1+D{last_row_num})*(1+C{last_row_num + 1})-1,"")',
        '',
        f'=B{last_row_num + 1}-B{last_row_num}-E{last_row_num + 1}',
        f'=IF(WEEKDAY(A{last_row_num + 1})=6,SUM(F{last_row_num -3}:F{last_row_num + 1}),)'
    ]

    sheet_instance.append_row(values, value_input_option='USER_ENTERED')


def main():
    update_spreadsheet(get_current_balance())
    

    
if __name__ == '__main__':
    main()