SELECT pose.time, pose.frame,
       position.x, position.y, position.z
FROM pose
JOIN position ON position.id = pose.position_id
ORDER BY pose.time;
