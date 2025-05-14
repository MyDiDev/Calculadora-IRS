import reflex as rx

class State(rx.State):
    worker: str = ""
    s_bruto: float = 0  
    r_isr: float = 0
    s_neto: float = 0
    afp: float = 0
    sfs: float = 0
    tss: float = 0
    bonificacion_v: float = 0
    bonificacion_res: str = ""
    added_discount: float = 0

    calculate_data: dict = {}
    
    disc_description: str = ""
    disc_value: str = ""
    disc_items: list[dict] = []

    bonificacion: bool = False
    discount: bool = False
    
    @rx.event
    def show_field(self, var:str):
        match var:
            case "bonificacion":
                self.bonificacion = True if not self.bonificacion else False
            case "discount":
                if not self.discount:
                    self.discount = True
                else:
                    self.discount = False
                    self.disc_items = []
            case _:
                print("Unvalid var name")
                return

    def add_discount_item(self) -> any:
        if self.disc_description and self.disc_value:
            self.disc_items.append({
                "id": max([item["id"] for item in self.disc_items],  default=0) + 1,
                "description": self.disc_description.capitalize(),
                "value":self.disc_value
            })
            self.disc_description = ""
            self.disc_value = "0"
            return
        yield rx.toast.error("Ingrese un Descuento Valido", close_button=True)
        print(self.disc_items)

    def del_item(self, id) -> None:
        self.disc_items = [item for item in self.disc_items if item["id"] != int(id)]

    def update_item(self, id, desc, value) -> None:
        for item in self.disc_items:
            if item["id"] == id:
                item["description"] = desc
                item["value"] = value

    
    @rx.event
    def calculate_salary(self, data:dict):
        print(data)
        if not data.get("empleado") or not data.get("s_bruto") or (self.bonificacion and not data.get("b_value")):
            yield rx.toast.error("Llene las entradas",  close_button=True)
            return

        try:
            self.worker = data["empleado"]
            self.s_bruto = float(data["s_bruto"])
            
            if self.s_bruto <= 0:
                yield rx.toast.error("Ingrese un Sueldo Bruto valido", close_button=True)
                return
            
            self.afp = self.s_bruto * 0.0304
            self.sfs = self.s_bruto * 0.0287
            self.tss = self.sfs + self.afp

            self.r_isr = self.calculate_isr(self.s_bruto)
            
            self.added_discount = self.s_bruto * (float(data["d_extra"]) / 100) if data.get("d_extra") else 0

            self.bonificacion_v = int(data["b_value"]) if data.get("b_value") else False
            
            if self.bonificacion_v and self.bonificacion:    
                if self.bonificacion_v < 1:
                    self.bonificacion_res = "No Aplica"
                elif self.bonificacion_v >= 1 and self.bonificacion_v <= 3:
                    self.bonificacion_res = f"Aplica un 10%, (Estimado: {round(self.s_bruto * 0.10, 2):,})."
                elif self.bonificacion_v >= 5 and self.bonificacion_v <= 10:
                    self.bonificacion_res = f"Aplica un 25%, (Estimado: {round(self.s_bruto * 0.25, 2):,})."
                else:
                    self.bonificacion_res = f"Aplica un 40%, (Estimado: {round(self.s_bruto * 0.40, 2):,})"
            else:
                self.bonificacion_res = "No Aplicado"

            self.s_neto = self.s_bruto - self.tss - self.r_isr + self.added_discount 

            self.calculate_data.update({"Sueldo Bruto: ":f"{self.s_bruto:,}"})
            self.calculate_data.update({"AFP: ":f"{round(self.afp,2):,}"})
            self.calculate_data.update({"SFS: ":f"{round(self.sfs,2):,}"})
            self.calculate_data.update({"ISR: ":f"{round(self.r_isr, 2):,}"})
            self.calculate_data.update({"Bonificacion: ":f"{self.bonificacion_res}"})
            self.calculate_data.update({"Sueldo Neto: ":f"{round(self.s_neto, 2):,}"})
            
            if self.discount:
                for discount in self.disc_items:
                    if discount["description"] and discount["value"]:
                        self.calculate_data.update({f"{discount['description']}: ":f"{float(discount['value']):,.2f}"})
                        self.s_neto -= float(discount["value"])

            for data, name in self.calculate_data.items():
                print(data, name)

            yield rx.toast.success("Calculos Exitosos!", close_button=True)
            
            self.bonificacion = False
            self.discount = False
            self.disc_items = []

        except Exception as e:
            yield rx.toast.success(f"Error Ocurrido: {e}", close_button=True)
            return

    def calculate_isr(self, salary: float) -> float:
        isr = 0
        amount: float = 0
        percentage: float = 0
        added: float = 0
        
        anual_salary = (salary - self.tss) * 12

        if anual_salary <= 416220.00:
            pass
        elif anual_salary >= 416220.01 and anual_salary <= 624329.00:
            percentage = 0.15
            amount = 416220.01
        elif anual_salary >= 624329.01 and anual_salary <= 867123.00:
            added = 31216.00
            percentage = 0.20
            amount = 624329.01
        else:
            added = 79776.00
            percentage = 0.25
            amount = 867123.01
        
        salary_calc = anual_salary - amount
        isr = (salary_calc * percentage) + added
        
        return isr / 12
            

def form_field(label: str, placeholder: str, type: str, name: str) -> rx.Component:
    return rx.form.field(
        rx.flex(
            rx.form.label(label),
            rx.form.control(
                rx.input(
                    placeholder=placeholder,
                    type=type,
                ),
                as_child=True,
            ),
            direction="column",
            spacing="1",
        ),
        name=name,
        width="100%",
    )


def base_page(child: rx.Component) -> rx.Component:
    return rx.flex(
        # nav goes here
        child,
        justify="center",
        align="center",
        direction="column",
        margin_y="10dvh",
        height="100%",
    )

def index() -> rx.Component:
    return base_page(
        rx.box(
            rx.tablet_and_desktop(
                rx.card(
                    rx.vstack(
                        rx.heading("Calcula los Descuentos del Salario", size="7"),
                        rx.separator(margin_y=".5em"),
                        rx.form.root(
                            rx.vstack(
                                form_field("Empleado:", "Ingrese el nombre del empleado", "text", "empleado"),
                                form_field("Sueldo Bruto:", "Ingrese el sueldo bruto del empleado", "number", "s_bruto"),
                                rx.flex(
                                    rx.checkbox("Aplicar Descuento", style={"cursor":"pointer"}, is_checked=State.discount, on_change=State.set_discount),
                                    rx.checkbox("Aplicar Bonificacion", style={"cursor":"pointer"}, is_checked=State.bonificacion, on_change=State.set_bonificacion),
                                    justify="between",
                                    align="center",
                                    spacing="9"
                                ),
                                rx.vstack(
                                    rx.cond(
                                        State.discount,
                                        rx.box(
                                            rx.text("Descripcion:"),
                                            rx.input(placeholder="Ingrese la descripcion del descuento", type="text", name="disc_description", value=State.disc_description, margin_y=".5em", on_change=State.set_disc_description),
                                            rx.hstack(
                                                rx.input(placeholder="Ingrese el monto a descontar", type="number", name="disc_value", value=State.disc_value, width="100%", margin_y=".5em",  on_change=State.set_disc_value),
                                                rx.button("Agregar Descuento", on_click=lambda: State.add_discount_item, margin_y=".5em", type="button"),
                                            ),
                                            rx.foreach(State.disc_items, lambda item: rx.card(
                                                rx.flex(
                                                    rx.vstack(
                                                        rx.text(f"{item['description']}:", size="2"),
                                                        rx.heading(f"{item['value']:,.2f} RD$", size="4"),
                                                    ),
                                                    rx.vstack(
                                                        rx.alert_dialog.root(
                                                            rx.alert_dialog.trigger(
                                                                rx.button("Eliminar", style={"background_color": "red"}, type="button", width="100%")
                                                            ),
                                                            rx.alert_dialog.content(
                                                                rx.heading("Seguro para eliminar este Descuento?"),
                                                                rx.text("Invocar esta accion puede eliminar el registro y no poder a volver conseguirlo."),
                                                                rx.flex(
                                                                    rx.alert_dialog.cancel(
                                                                        rx.button("Cancelar"),
                                                                    ),
                                                                    rx.alert_dialog.action(
                                                                        rx.button("Eliminar", style={"background_color":"red"}, on_click=lambda: State.del_item(item["id"]))
                                                                    ),
                                                                    spacing="3",
                                                                )
                                                            )
                                                        ),
                                                        rx.button("Editar",type="button",on_click=lambda: State.update_item(item["id"], State.disc_description, State.disc_value), width="100%"),
                                                    ),
                                                    justify="between",
                                                    size="2"
                                                ),
                                                margin_y=".5em",
                                            )),
                                            width="100%",
                                            margin_top=".5em"
                                        ),
                                        None
                                    ),
                                    rx.cond(
                                        State.bonificacion,
                                        form_field("Años en la Empresa", "Ingrese la cantidad de años en la empresa", "number", "b_value"),
                                        None
                                    ),
                                    width="100%",
                                )
                            ),
                            rx.dialog.root(
                                rx.dialog.trigger(
                                    rx.button(
                                        "Calcular",
                                        style={"cursor":"pointer"},
                                        width="100%",
                                        margin_y="1em",
                                        type="submit",
                                    )
                                ),
                                rx.dialog.content(
                                    rx.dialog.title("Resultados del Calculo", margin_y=".5em"),
                                    rx.dialog.description(
                                        rx.vstack(
                                            rx.text(f"Empleado: {State.worker}"),
                                            rx.foreach(State.calculate_data.items(), lambda data: rx.box(
                                                rx.text(f"{data[0]} {data[1]}"),
                                            ))
                                        )
                                    ),
                                    rx.dialog.close(
                                        rx.button("Cerrar Resultados", margin_y="1em", style={"cursor":"pointer"})
                                    )
                                ),
                            ),
                            width="100%",
                            on_submit=State.calculate_salary,
                            reset_on_submit=False,
                        ),
                    ),   
                    min_width="370px",
                    padding="1em",
                ),
            ),
            rx.mobile_only(
                rx.card(
                    rx.vstack(
                        rx.heading("Calcula los Descuentos del Salario", size="7"),
                        rx.separator(margin_y=".5em"),
                        rx.form.root(
                            rx.vstack(
                                form_field("Empleado:", "Ingrese el nombre del empleado", "text", "empleado"),
                                form_field("Sueldo Bruto:", "Ingrese el sueldo bruto del empleado", "number", "s_bruto"),
                                rx.flex(
                                    rx.checkbox("Aplicar Descuento", style={"cursor":"pointer"}, is_checked=State.discount, on_change=State.set_discount),
                                    rx.checkbox("Aplicar Bonificacion", style={"cursor":"pointer"}, is_checked=State.bonificacion, on_change=State.set_bonificacion),
                                    justify="between",
                                    align="center",
                                    spacing="9"
                                ),
                                rx.vstack(
                                    rx.cond(
                                        State.discount,
                                        rx.box(
                                            rx.text("Descripcion:", value=State.disc_description),
                                            rx.input(placeholder="Ingrese la descripcion del descuento", type="text", name="disc_description", value=State.disc_description, margin_y=".5em", on_change=State.set_disc_description),
                                            rx.hstack(
                                                rx.input(placeholder="Ingrese el monto a descontar", type="number", name="disc_value", value=State.disc_value, width="100%", margin_y=".5em", on_change=State.set_disc_value),
                                                rx.button("Agregar Descuento", on_click=lambda: State.add_discount_item, margin_y=".5em", type="button"),
                                            ),
                                            rx.cond(
                                                State.disc_items,
                                                rx.foreach(State.disc_items, lambda item: rx.card(
                                                    rx.flex(
                                                        rx.vstack(
                                                            rx.text(f"{item['description']}:", size="2"),
                                                            rx.heading(f"{item['value']:,.2f} RD$", size="4"),
                                                        ),
                                                        rx.vstack(
                                                            rx.alert_dialog.root(
                                                                rx.alert_dialog.trigger(
                                                                    rx.button("Eliminar", style={"background_color": "red", "cursor":"pointer"}, type="button", width="100%")
                                                                ),
                                                                rx.alert_dialog.content(
                                                                    rx.heading("Seguro para eliminar este Descuento?"),
                                                                    rx.text("Invocar esta accion puede eliminar el registro y no poder a volver conseguirlo."),
                                                                    rx.flex(
                                                                        rx.alert_dialog.cancel(
                                                                            rx.button("Cancelar"),
                                                                        ),
                                                                        rx.alert_dialog.action(
                                                                            rx.button("Eliminar", style={"background_color":"red"}, on_click=lambda: State.del_item(item["id"]))
                                                                        ),
                                                                        spacing="3",
                                                                    )
                                                                ),
                                                            ),
                                                            rx.button("Editar", type="button",on_click=lambda: State.update_item(item["id"], State.disc_description, State.disc_value), width="100%"),
                                                        ),
                                                        justify="between",
                                                        size="2",
                                                    ),
                                                    margin_y=".5em"
                                                )),
                                            ),
                                            width="100%",                                            
                                        ),
                                        None
                                    ),
                                    rx.cond(
                                        State.bonificacion,
                                        form_field("Años en la Empresa", "Ingrese la cantidad de años en la empresa", "number", "b_value"),
                                        None
                                    ),
                                    width="100%",
                                )
                            ),
                            rx.dialog.root(
                                rx.dialog.trigger(
                                    rx.button(
                                        "Calcular",
                                        style={"cursor":"pointer"},
                                        width="100%",
                                        margin_y="1em",
                                        type="submit",
                                    )
                                ),
                                rx.dialog.content(
                                    rx.dialog.title("Resultados del Calculo", margin_y=".5em"),
                                    rx.dialog.description(
                                        rx.vstack(
                                            rx.text(f"Empleado: {State.worker}"),
                                            rx.foreach(State.calculate_data.items(), lambda data: rx.box(
                                                rx.text(f"{data[0]} {data[1]}"),
                                            ))
                                        )
                                    ),
                                    rx.dialog.close(
                                        rx.button("Cerrar Resultados", margin_y="1em", style={"cursor":"pointer"})
                                    )
                                ),
                            ),
                            width="100%",
                            on_submit=State.calculate_salary,
                            reset_on_submit=False,
                        ),
                    ),   
                    min_width="250px",
                    padding="1em",
                ),
            ),
        )
    ),
    