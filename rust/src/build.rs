use eyre::Result;

fn main() -> Result<()> {
    prost_build::compile_protos(
        &["../schemas/swap_event.proto"],
        &["../schemas"],
    )?;
    Ok(())
}
