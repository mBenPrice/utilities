import xlrd

workbook = xlrd.open_workbook('test.xlsx')


#####################################
#
#  A few simple ways of printing data from a MS Excel
#  spreadsheet.  I like to run each on a spreadsheet and pick
#  the one that is closest to the output I want when a script
#  needs to read a .xlsx file.
#
#####################################


for sheet in workbook.sheet_names():
    print '\n\n', sheet
    worksheet = workbook.sheet_by_name(sheet)

    for idx in range(0, worksheet.nrows):
        for col in worksheet.row(idx):
            t_col = str(col)
            print t_col[t_col.find("'")+1:t_col.find("'")+ \
                        1+t_col[t_col.find("'")+1:].find("'")],
        print ''


for sheet in workbook.sheet_names():
    print '\n\n', sheet
    worksheet = workbook.sheet_by_name(sheet)

    for idx in range(0, worksheet.nrows):
        for col in worksheet.row(idx):
            print col
        print ''


for sheet in workbook.sheet_names():
    print '\n', sheet
    worksheet = workbook.sheet_by_name(sheet)

    for r_idx in range(0, worksheet.nrows):
        print 'Row:', r_idx
        for c_idx in range(0, worksheet.ncols):
            cell_type = worksheet.cell_type(r_idx, c_idx)
            cell_value = worksheet.cell_value(r_idx, c_idx)
            print '	', cell_type, ':', cell_value
