"""Interface desktop autônoma do SellFlow."""
import os
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

base_dir = Path(os.getenv("LOCALAPPDATA", Path.home())) / "SellFlow"
os.environ["STANDALONE_MODE"] = "true"
os.environ["STANDALONE_DATA_DIR"] = str(base_dir)

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QComboBox, QDateEdit, QDialog, QDoubleSpinBox,
    QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox,
    QPushButton, QSpinBox, QStackedWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)
from sqlalchemy import func, select

import app.models
from app.database.base import Base
from app.database.connection import SessionLocal, engine
from app.models.categoria import Categoria
from app.models.produto import Produto
from app.models.operacao import Cliente, Lote, MovimentacaoEstoque, Usuario, Venda, VendaItem
from app.services.security import hash_password


APP_STYLE = """
QMainWindow { background: #f6f8fc; } QWidget { font-family: Segoe UI; font-size: 13px; color: #1e293b; }
QFrame#sidebar { background: #102a43; } QLabel#brand { color: white; font-size: 24px; font-weight: 700; }
QLabel#subtitle { color: #a7c7e7; } QPushButton#nav { color: #d9eafa; text-align: left; padding: 12px 16px; border: 0; border-radius: 6px; }
QPushButton#nav:hover, QPushButton#nav:checked { background: #1f4d78; color: white; }
QPushButton#primary { background: #137c8b; color: white; border: 0; border-radius: 6px; padding: 9px 15px; font-weight: 600; }
QPushButton#primary:hover { background: #0f6672; } QTableWidget { background: white; border: 1px solid #dbe4ee; border-radius: 6px; gridline-color: #edf2f7; }
QHeaderView::section { background: #edf3f8; padding: 8px; border: 0; font-weight: 600; } QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox, QSpinBox { background: white; border: 1px solid #cbd5e1; border-radius: 5px; padding: 7px; } QLabel#title { font-size: 25px; font-weight: 700; } QLabel#card { background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 18px; font-size: 16px; }
"""

def db(): return SessionLocal()
def item(text): return QTableWidgetItem(str(text if text is not None else ""))

class ProductDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent); self.setWindowTitle("Novo produto"); self.setMinimumWidth(420)
        form = QFormLayout(self); self.nome = QLineEdit(); self.ean = QLineEdit(); self.principio = QLineEdit(); self.fabricante = QLineEdit(); self.categoria = QComboBox()
        self.custo = QDoubleSpinBox(); self.venda = QDoubleSpinBox()
        for field in (self.custo, self.venda): field.setMaximum(999999); field.setDecimals(2)
        s = db()
        try:
            for cat in s.scalars(select(Categoria).order_by(Categoria.nome)): self.categoria.addItem(cat.nome, cat.id)
        finally: s.close()
        form.addRow("Nome", self.nome); form.addRow("Categoria", self.categoria); form.addRow("EAN", self.ean); form.addRow("Princípio ativo", self.principio); form.addRow("Fabricante", self.fabricante); form.addRow("Custo", self.custo); form.addRow("Preço de venda", self.venda)
        save = QPushButton("Salvar"); save.setObjectName("primary"); save.clicked.connect(self.accept); form.addRow(save)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); Base.metadata.create_all(engine); self.setWindowTitle("SellFlow — Gestão para Farmácias"); self.resize(1240, 760); self.setStyleSheet(APP_STYLE)
        root = QWidget(); self.setCentralWidget(root); layout = QHBoxLayout(root); layout.setContentsMargins(0,0,0,0); layout.setSpacing(0)
        side = QFrame(); side.setObjectName("sidebar"); side.setFixedWidth(220); side_layout = QVBoxLayout(side); side_layout.setContentsMargins(14,20,14,20)
        brand = QLabel("SellFlow"); brand.setObjectName("brand"); sub = QLabel("GESTÃO PARA FARMÁCIAS"); sub.setObjectName("subtitle"); side_layout.addWidget(brand); side_layout.addWidget(sub); side_layout.addSpacing(28)
        self.stack = QStackedWidget(); names = [("Dashboard", self.dashboard_page), ("Produtos", self.products_page), ("Clientes", self.clients_page), ("Estoque por lotes", self.stock_page), ("PDV / Vendas", self.sales_page), ("Usuários", self.users_page)]
        for index, (name, maker) in enumerate(names):
            button = QPushButton(name); button.setObjectName("nav"); button.clicked.connect(lambda _, i=index: self.open_page(i)); side_layout.addWidget(button); self.stack.addWidget(maker())
        side_layout.addStretch(); side_layout.addWidget(QLabel("Versão local 1.0")); layout.addWidget(side); layout.addWidget(self.stack, 1); self.open_page(0)

    def page(self, title, action_text=None, action=None):
        page = QWidget(); outer = QVBoxLayout(page); outer.setContentsMargins(32,28,32,28); top = QHBoxLayout(); label = QLabel(title); label.setObjectName("title"); top.addWidget(label); top.addStretch()
        if action_text: b=QPushButton(action_text); b.setObjectName("primary"); b.clicked.connect(action); top.addWidget(b)
        outer.addLayout(top); return page, outer

    def open_page(self, index): self.stack.setCurrentIndex(index); self.refresh_all()
    def refresh_all(self):
        for method in (self.refresh_dashboard, self.refresh_products, self.refresh_clients, self.refresh_stock, self.refresh_sales, self.refresh_users):
            try: method()
            except Exception: pass

    def dashboard_page(self):
        page, layout = self.page("Visão geral"); self.dashboard_cards = QHBoxLayout(); layout.addLayout(self.dashboard_cards); layout.addStretch(); return page
    def refresh_dashboard(self):
        while self.dashboard_cards.count(): w=self.dashboard_cards.takeAt(0).widget(); w and w.deleteLater()
        s=db()
        try:
            data=[("Produtos ativos", s.scalar(select(func.count()).select_from(Produto).where(Produto.ativo==True))), ("Clientes", s.scalar(select(func.count()).select_from(Cliente))), ("Lotes em estoque", s.scalar(select(func.count()).select_from(Lote).where(Lote.quantidade>0))), ("Vendas realizadas", s.scalar(select(func.count()).select_from(Venda)))]
        finally: s.close()
        for title, value in data: lab=QLabel(f"<b>{title}</b><br><font size='+3'><b>{value}</b></font>"); lab.setObjectName("card"); lab.setMinimumWidth(190); self.dashboard_cards.addWidget(lab)

    def products_page(self):
        page, layout = self.page("Produtos", "Novo produto", self.new_product); self.products_table=QTableWidget(); self.products_table.setColumnCount(7); self.products_table.setHorizontalHeaderLabels(["ID","Nome","Categoria","EAN","Princípio ativo","Venda","Status"]); self.products_table.setEditTriggers(QTableWidget.NoEditTriggers); layout.addWidget(self.products_table); return page
    def refresh_products(self):
        if not hasattr(self,'products_table'): return
        s=db()
        try: rows=s.scalars(select(Produto).order_by(Produto.nome)).all(); self.products_table.setRowCount(len(rows));
        finally: s.close()
        for r,p in enumerate(rows):
            cat=s if False else None
            for c,v in enumerate([p.id,p.nome,p.categoria_id,p.codigo_barras,p.principio_ativo,f"R$ {p.preco_venda}","Ativo" if p.ativo else "Inativo"]): self.products_table.setItem(r,c,item(v))
        self.products_table.resizeColumnsToContents()
    def new_product(self):
        if not db().scalar(select(func.count()).select_from(Categoria)): self.new_category()
        dialog=ProductDialog(self)
        if dialog.exec() and dialog.nome.text().strip() and dialog.categoria.currentData():
            s=db(); p=Produto(nome=dialog.nome.text().strip(), categoria_id=dialog.categoria.currentData(), codigo_barras=dialog.ean.text() or None, principio_ativo=dialog.principio.text() or None, fabricante=dialog.fabricante.text() or None, preco_custo=Decimal(str(dialog.custo.value())), preco_venda=Decimal(str(dialog.venda.value())), estoque_minimo=0, ativo=True); s.add(p); s.commit(); s.close(); self.refresh_products()
    def new_category(self):
        name, ok = self.simple_prompt("Nova categoria", "Nome da categoria")
        if ok and name: s=db(); s.add(Categoria(nome=name)); s.commit(); s.close()
    def simple_prompt(self,title,label):
        d=QDialog(self); d.setWindowTitle(title); f=QFormLayout(d); e=QLineEdit(); f.addRow(label,e); b=QPushButton("Salvar"); b.setObjectName("primary"); b.clicked.connect(d.accept); f.addRow(b); return (e.text(), True) if d.exec() else ("",False)

    def clients_page(self):
        page,layout=self.page("Clientes", "Novo cliente", self.new_client); self.clients_table=QTableWidget(); self.clients_table.setColumnCount(4); self.clients_table.setHorizontalHeaderLabels(["ID","Nome","CPF/CNPJ","Telefone"]); layout.addWidget(self.clients_table); return page
    def refresh_clients(self):
        if not hasattr(self,'clients_table'): return
        s=db(); rows=s.scalars(select(Cliente).order_by(Cliente.nome)).all(); s.close(); self.clients_table.setRowCount(len(rows))
        for r,x in enumerate(rows):
            for c,v in enumerate([x.id,x.nome,x.cpf_cnpj,x.telefone]): self.clients_table.setItem(r,c,item(v))
        self.clients_table.resizeColumnsToContents()
    def new_client(self):
        d=QDialog(self); d.setWindowTitle("Novo cliente"); f=QFormLayout(d); name=QLineEdit(); doc=QLineEdit(); phone=QLineEdit(); f.addRow("Nome",name);f.addRow("CPF/CNPJ",doc);f.addRow("Telefone",phone); b=QPushButton("Salvar");b.setObjectName("primary");b.clicked.connect(d.accept);f.addRow(b)
        if d.exec() and name.text().strip(): s=db();s.add(Cliente(nome=name.text().strip(),cpf_cnpj=doc.text() or None,telefone=phone.text() or None));s.commit();s.close();self.refresh_clients()

    def stock_page(self):
        page,layout=self.page("Estoque por lotes", "Novo lote", self.new_lot); self.stock_table=QTableWidget(); self.stock_table.setColumnCount(6); self.stock_table.setHorizontalHeaderLabels(["Produto","Lote","Validade","Localização","Quantidade","Custo"]);layout.addWidget(self.stock_table);return page
    def refresh_stock(self):
        if not hasattr(self,'stock_table'):return
        s=db();rows=s.scalars(select(Lote).order_by(Lote.validade)).all(); products={p.id:p.nome for p in s.scalars(select(Produto)).all()};s.close();self.stock_table.setRowCount(len(rows))
        for r,x in enumerate(rows):
            for c,v in enumerate([products.get(x.produto_id),x.codigo,x.validade,x.localizacao,x.quantidade,f"R$ {x.custo_unitario}"]):self.stock_table.setItem(r,c,item(v))
        self.stock_table.resizeColumnsToContents()
    def new_lot(self):
        s=db(); products=s.scalars(select(Produto).where(Produto.ativo==True).order_by(Produto.nome)).all();s.close()
        if not products: QMessageBox.warning(self,"Sem produtos","Cadastre um produto antes de criar lotes.");return
        d=QDialog(self);d.setWindowTitle("Novo lote");f=QFormLayout(d);p=QComboBox();[p.addItem(x.nome,x.id) for x in products];code=QLineEdit();valid=QDateEdit(date.today());valid.setCalendarPopup(True);loc=QLineEdit();q=QDoubleSpinBox();cost=QDoubleSpinBox()
        for x in(q,cost):x.setMaximum(999999);x.setDecimals(3)
        f.addRow("Produto",p);f.addRow("Código do lote",code);f.addRow("Validade",valid);f.addRow("Localização",loc);f.addRow("Quantidade",q);f.addRow("Custo",cost);b=QPushButton("Salvar");b.setObjectName("primary");b.clicked.connect(d.accept);f.addRow(b)
        if d.exec() and code.text() and q.value()>0:
            s=db();x=Lote(produto_id=p.currentData(),codigo=code.text(),validade=valid.date().toPython(),localizacao=loc.text() or None,quantidade=Decimal(str(q.value())),custo_unitario=Decimal(str(cost.value())));s.add(x);s.flush();s.add(MovimentacaoEstoque(lote_id=x.id,tipo="entrada",quantidade=x.quantidade,origem="cadastro",observacao="Saldo inicial"));s.commit();s.close();self.refresh_stock()

    def sales_page(self):
        page,layout=self.page("PDV / Vendas"); form=QHBoxLayout();self.sale_product=QComboBox();self.sale_customer=QComboBox();self.sale_user=QComboBox();self.sale_qty=QDoubleSpinBox();self.sale_qty.setMinimum(1);self.sale_qty.setMaximum(9999);self.sale_qty.setValue(1);self.sale_payment=QComboBox();self.sale_payment.addItems(["Dinheiro","Cartão","PIX","Convênio"]);go=QPushButton("Finalizar venda");go.setObjectName("primary");go.clicked.connect(self.make_sale)
        for label,widget in [("Produto",self.sale_product),("Cliente",self.sale_customer),("Usuário",self.sale_user),("Qtd.",self.sale_qty),("Pagamento",self.sale_payment)]:form.addWidget(QLabel(label));form.addWidget(widget)
        form.addWidget(go);layout.addLayout(form);self.sales_table=QTableWidget();self.sales_table.setColumnCount(5);self.sales_table.setHorizontalHeaderLabels(["Venda","Data","Cliente","Pagamento","Total"]);layout.addWidget(self.sales_table);return page
    def refresh_sales(self):
        if not hasattr(self,'sales_table'):return
        s=db(); products=s.scalars(select(Produto).where(Produto.ativo==True)).all();clients=s.scalars(select(Cliente).order_by(Cliente.nome)).all();users=s.scalars(select(Usuario).where(Usuario.ativo==True)).all();sales=s.scalars(select(Venda).order_by(Venda.criado_em.desc())).all();cmap={c.id:c.nome for c in clients};s.close()
        for combo,rows in [(self.sale_product,products),(self.sale_customer,clients),(self.sale_user,users)]: combo.clear();
        self.sale_customer.addItem("Consumidor final",None)
        for x in products:self.sale_product.addItem(x.nome,x.id)
        for x in clients:self.sale_customer.addItem(x.nome,x.id)
        for x in users:self.sale_user.addItem(x.nome,x.id)
        self.sales_table.setRowCount(len(sales))
        for r,x in enumerate(sales):
            for c,v in enumerate([x.id,x.criado_em.strftime('%d/%m/%Y %H:%M'),cmap.get(x.cliente_id,"Consumidor final"),x.forma_pagamento,f"R$ {x.total}"]):self.sales_table.setItem(r,c,item(v))
        self.sales_table.resizeColumnsToContents()
    def make_sale(self):
        if not self.sale_product.currentData() or not self.sale_user.currentData():QMessageBox.warning(self,"Dados necessários","Cadastre produto e usuário antes de vender.");return
        s=db(); product=s.get(Produto,self.sale_product.currentData());qty=Decimal(str(self.sale_qty.value()));lots=s.scalars(select(Lote).where(Lote.produto_id==product.id,Lote.quantidade>0,Lote.validade>=date.today()).order_by(Lote.validade)).all()
        if sum((x.quantidade for x in lots),Decimal('0'))<qty:s.close();QMessageBox.warning(self,"Estoque insuficiente",f"Não há estoque suficiente para {product.nome}.");return
        sale=Venda(cliente_id=self.sale_customer.currentData(),usuario_id=self.sale_user.currentData(),status="concluida",forma_pagamento=self.sale_payment.currentText(),total=Decimal('0'));s.add(sale);s.flush();remaining=qty;total=Decimal('0')
        for lot in lots:
            take=min(remaining,lot.quantidade);lot.quantidade-=take;remaining-=take;total+=take*product.preco_venda;s.add(VendaItem(venda_id=sale.id,lote_id=lot.id,produto_id=product.id,quantidade=take,preco_unitario=product.preco_venda));s.add(MovimentacaoEstoque(lote_id=lot.id,tipo="saida",quantidade=take,origem="venda",observacao=f"Venda {sale.id}"))
            if remaining==0:break
        sale.total=total;s.commit();s.close();QMessageBox.information(self,"Venda concluída",f"Venda #{sale.id} registrada. Total: R$ {total}");self.refresh_all()

    def users_page(self):
        page,layout=self.page("Usuários", "Novo usuário", self.new_user);self.users_table=QTableWidget();self.users_table.setColumnCount(3);self.users_table.setHorizontalHeaderLabels(["Nome","E-mail","Perfil"]);layout.addWidget(self.users_table);return page
    def refresh_users(self):
        if not hasattr(self,'users_table'):return
        s=db();rows=s.scalars(select(Usuario).order_by(Usuario.nome)).all();s.close();self.users_table.setRowCount(len(rows))
        for r,x in enumerate(rows):
            for c,v in enumerate([x.nome,x.email,x.perfil]):self.users_table.setItem(r,c,item(v))
        self.users_table.resizeColumnsToContents()
    def new_user(self):
        d=QDialog(self);d.setWindowTitle("Novo usuário");f=QFormLayout(d);name=QLineEdit();email=QLineEdit();password=QLineEdit();password.setEchoMode(QLineEdit.Password);role=QComboBox();role.addItems(["administrador","gerente","operador"]);f.addRow("Nome",name);f.addRow("E-mail",email);f.addRow("Senha",password);f.addRow("Perfil",role);b=QPushButton("Salvar");b.setObjectName("primary");b.clicked.connect(d.accept);f.addRow(b)
        if d.exec() and name.text() and email.text() and len(password.text())>=8:
            s=db();s.add(Usuario(nome=name.text(),email=email.text().lower(),senha_hash=hash_password(password.text()),perfil=role.currentText(),ativo=True));s.commit();s.close();self.refresh_users()

if __name__ == "__main__":
    app=QApplication(sys.argv);app.setApplicationName("SellFlow");window=MainWindow();window.show();sys.exit(app.exec())
