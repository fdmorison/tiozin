# Tiozin Family: Understanding Tios and Tiozins

<p align="center">
  <img
    src="https://raw.githubusercontent.com/fdmorison/tiozin/main/docs/img/tiozin_family.jpeg"
    alt="Tiozin Family"
  />
</p>

When we say **Tiozin Family**, it’s not just cute — it’s the architectural model of the framework.

The banner illustrates this idea: a family.

- The larger characters represent the **Tios and Tias**.
- The smaller ones represent the **Tiozins**.

This family metaphor is not decorative — it defines how the system is structured.

---

## 🧔 What is a Tio or Tia?

A **Tio** or **Tia** is a provider family. Many families together form the ecosystem.

Each Tio represents a technological domain and runtime. Imagine examples like:

- Tio Spark → distributed processing integration
- Tio DuckDB → embedded analytics integration
- Tia Google → cloud-native integration

A Tio defines:

- How it integrates with data systems
- The execution semantics and rules
- The plugins, called Tiozins, that interact with data
- The namespace where its Tiozins live

A Tio does not execute work directly — it is a provider.

Like any family, it creates and maintains its members: the Tiozins. The ecosystem grows as new families appear.

You can create public or private provider families. You can even create your own, with your own name:

- Tio Dilbert
- Tia Maria

And nothing stops you from creating your own :)

---

## 👶 What is a Tiozin?

A **Tiozin** is a plugin offered by a Tio or Tia. It is the smallest unit of work in the ecosystem.

If it exists in the execution model, it is a Tiozin. If it is pluggable, it is a Tiozin.

- Jobs are Tiozins.
- Runners are Tiozins.
- Metadata registries are Tiozins.
- Inputs, Outputs, Transforms, all are Tiozins.

Tiozins are designed to be small, specialized, composable, and testable. They do one thing well.

The power of the system comes from composing many focused plugins together.

---

## 🌱 The Big Will

Tiozin does not want to do everything. It is not a single engine attempting to control everything.

It exists to connect things.

It is the glue between independent provider families, allowing open-source development to scale:

- Provider families evolve independently
- Plugins multiply and specialize
- Everything remains modular, replaceable, and testable

No monolith.
Just explicit families and pluggable members.

You are welcome to contribute to the core, and to build your own providers — private or public.
And if Tiozin makes a difference in your work, you are welcome to reference it ❤️

As a developer, I believe the family grows when people build.

---

## ✨ In One Line

A **Tio** provides.
A **Tiozin** executes.
And everything belongs to a family.
