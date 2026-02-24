
fn main() {
    prost_build::compile_protos(
        &["../schemas/swap_event.proto"],
        &["../schemas/"],
    )
    .expect("Failed to compile protobufs");
}
