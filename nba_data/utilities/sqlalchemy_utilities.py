def bulk_insert_records(engine, data_instances, sql_tbl_class, batchsize=250000):
    if data_instances is not None:
        for i in range(0, len(data_instances), batchsize):
            engine.execute(sql_tbl_class.__table__.insert(),
                           [get_bulk_instance(instance, sql_tbl_class) for instance in
                            data_instances[i:i + batchsize]])
    table_name = sql_tbl_class.__table__.name
    log_note = 'Inserted {} records in {}'.format(len(data_instances), table_name)
    return log_note

def get_bulk_instance(instance_data, sql_tbl_class):
    instance_record = create_instance_record(sql_tbl_class)
    for key, value in instance_data.items():
        if key in instance_record:
            instance_record[key] = value
    return instance_record

def create_instance_record(sql_tbl_class):
    instance_record = {}
    for col in sql_tbl_class.__table__.c:
        if not col.primary_key:
            if col.default is not None:
                instance_record.update({col.name: col.default.arg})
            else:
                instance_record.update({col.name: None})
    return instance_record

def get_row_dict(row):
    return row._asdict()
