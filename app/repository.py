from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.schemas import UserCreate, UserUpdate


class UserRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_users(self):

        result = await self.session.execute(
            select(User)
        )

        return result.scalars().all()

    async def get_user(self, user_id: int):

        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )

        return result.scalar_one_or_none()

    async def create_user(
        self,
        user_data: UserCreate
    ):

        async with self.session.begin():

            user = User(
                name=user_data.name,
                email=user_data.email
            )

            self.session.add(user)

        await self.session.refresh(user)

        return user

    async def update_user(
        self,
        user_id: int,
        user_data: UserUpdate
    ):

        async with self.session.begin():

            user = await self.get_user(user_id)

            if not user:
                return None

            if user_data.name is not None:
                user.name = user_data.name

            if user_data.email is not None:
                user.email = user_data.email

        await self.session.refresh(user)

        return user

    async def delete_user(self, user_id: int):

        async with self.session.begin():

            user = await self.get_user(user_id)

            if not user:
                return False

            await self.session.delete(user)

        return True
    
    #ofahmet repositoryimi sal 