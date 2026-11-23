classes = [GripperPose, Point, Quaternion]
ormatic = ORMatic(
    class_dependency_graph=ClassDiagram(classes=classes)
)
ormatic.make_all_tables()
ormatic.to_sqlalchemy_file(file=file)
