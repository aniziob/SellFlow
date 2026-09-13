from pydantic import BaseModel, ConfigDict


class CategoriaBase(BaseModel):
    nome: str
    descricao: str | None = None


class CategoriaCreate(CategoriaBase):
    pass


class CategoriaResponse(CategoriaBase):
    id: int

    model_config = ConfigDict(
        from_attributes=True,
    )
