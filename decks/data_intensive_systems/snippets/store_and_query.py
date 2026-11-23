session.add_all([to_dao(pose) for pose in poses])
session.commit()

pose = variable(type_=GripperPose, domain=[])
query = an(entity(pose).where(pose.position.z < 0.85))
rows = eql_to_sql(query, session).evaluate()
low_poses = [row.from_dao() for row in rows]
