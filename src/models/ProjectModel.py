from functools import total_ordering
import re
from turtle import reset

from openai import project
from .BaseDataModel import BaseDataModel
from .db__schemes import Project
from .enums.DataBaseEnum import DataBaseEnum
from sqlalchemy.future import select
from sqlalchemy import func

class ProjectModel(BaseDataModel):
    def __init__(self, db_client:object):
        super().__init__(db_client=db_client)
        self.db_client = db_client
    @classmethod
    async def create_instance(cls,db_client:object):


        
        instance = cls(db_client)
        return instance


    async def creat_project(self,project:Project):
        
        async with self.db_client() as session: # type: ignore
            async with session.begin():
                session.add(project)
            await session.commit()
            await session.refresh(project)
        return project
        # result = await self.collection.insert_one(project.dict(by_alias = True,exclude_unset=True))
        # project.id = result.inserted_id
        # return project
    
    async def get_project_or_create_one(self,project_id:int):

        async with self.db_client() as session: # type: ignore
            async with session.begin():
                result = await session.execute(
                    select(Project).where(Project.project_id == project_id)
                )
                project = result.scalar_one_or_none()
                if project is None:
                    project_rec = Project(
                        project_id = project_id
                    )
                    project =await self.creat_project(project=project_rec)
                    return project
                else:
                    return project
        # record = await self.collection.find_one({"project_id":project_id})
        # if record is None:
        #     ## creat new project
        #     project = Project(project_id=project_id) # type: ignore
        #     project = await self.creat_project(project=project)
        #     return project
        
        # return Project(**record)
    
    async def get_all_project(self, page:int=1,page_size:int =10):
        async with self.db_client() as session: # type: ignore
            async with session.begin():
                total_documents = await session.execute(select(func.count(Project.project_id))).scaler_one()
                total_pages = total_documents//page_size                
                if total_documents % page_size>0:
                    total_pages +=1

                query = select(Project).offset((page-1)*page_size).limit(page_size)
                projects =await session.execute( query).scalars().all()
                return projects,total_pages

        # count total number of all documents
        # total_documents = self.collection.count_documents({})

        # total_pages = total_documents//page_size
        # if total_documents % page_size>0:
        #     total_pages +=1

        # cursor=await self.collection.find().skip((page-1)*(page_size)).limit(page_size)
        # projects= []
        # for document in cursor:
        #     projects.append(
        #         Project(**document)
        #     )

        # return projects,total_pages