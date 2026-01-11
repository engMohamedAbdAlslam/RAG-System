from .BaseDataModel import BaseDataModel
from .db__schemes import Project
from .enums.DataBaseEnum import DataBaseEnum

class ProjectModel(BaseDataModel):
    def __init__(self, db_client:object):
        super().__init__(db_client=db_client)
        self.collection = self.db_client[DataBaseEnum.COLLECTION_PROJECT_NAME.value] # type: ignore
    @classmethod
    async def create_instance(cls,db_client:object):
        instance = cls(db_client)
        await instance.init_collection()
        return instance



    async def init_collection(self):
        all_collections =await self.db_client.list_collection_names() # type: ignore
        if DataBaseEnum.COLLECTION_PROJECT_NAME.value not in all_collections:
            self.collection=self.db_client[DataBaseEnum.COLLECTION_PROJECT_NAME.value] # type: ignore
            indexes = Project.get_indexes()
            for index in indexes:
                await self.collection.create_index(
                    index["key"],
                    name = index["name"],
                    unique = index["unique"]
                )


    async def creat_project(self,project:Project):
        result = await self.collection.insert_one(project.dict(by_alias = True,exclude_unset=True))
        project.id = result.inserted_id
        return project
    
    async def get_project_or_create_one(self,project_id:str):
        record = await self.collection.find_one({"project_id":project_id})
        if record is None:
            ## creat new project
            project = Project(project_id=project_id) # type: ignore
            project = await self.creat_project(project=project)
            return project
        
        return Project(**record)
    
    async def get_all_project(self, page:int=1,page_size:int =10):

        # count total number of all documents
        total_documents = self.collection.count_documents({})

        total_pages = total_documents//page_size
        if total_documents % page_size>0:
            total_pages +=1

        cursor=await self.collection.find().skip((page-1)*(page_size)).limit(page_size)
        projects= []
        for document in cursor:
            projects.append(
                Project(**document)
            )

        return projects,total_pages