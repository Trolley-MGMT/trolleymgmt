db.createUser(
    {
        user: "admin",
        pwd: "s3cr3t",
        roles: [
            {
                role: "readWrite",
                db: "admin"
            }
        ]
    }
);
db.createCollection("test"); //MongoDB creates the database when you first store data in that database