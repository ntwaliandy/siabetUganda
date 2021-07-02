CREATE TRIGGER insert_trigger
BEFORE INSERT ON group_members
FOR EACH ROW
SET new.unid = CONCAT(new.group_id,new.user_id);